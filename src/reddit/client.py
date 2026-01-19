"""Reddit JSON API client with rate limiting."""

import asyncio
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import get_settings
from src.reddit.rate_limiter import AdaptiveRateLimiter
from src.reddit.parsers import (
    extract_comments_from_post_page,
    extract_post_listing,
    parse_author,
    parse_comments_tree,
    parse_post,
    parse_subreddit_about,
)


class RedditAPIError(Exception):
    """Custom exception for Reddit API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RedditClient:
    """Async client for Reddit JSON API with rate limiting.

    This client uses the public JSON API (no authentication required)
    and implements rate limiting to avoid being blocked.
    """

    BASE_URL = "https://www.reddit.com"

    def __init__(
        self,
        requests_per_minute: int = 30,
        user_agent: Optional[str] = None,
    ):
        """Initialize the Reddit client.

        Args:
            requests_per_minute: Maximum requests per minute.
            user_agent: Custom user agent string.
        """
        settings = get_settings()
        self.user_agent = user_agent or settings.reddit_user_agent
        self.rate_limiter = AdaptiveRateLimiter(requests_per_minute)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "RedditClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=30.0,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.user_agent},
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(self, url: str) -> dict[str, Any]:
        """Make a rate-limited request to Reddit API.

        Args:
            url: Full URL to request.

        Returns:
            Parsed JSON response.

        Raises:
            RedditAPIError: If the request fails.
        """
        await self.rate_limiter.acquire()

        response = await self.client.get(url)

        # Update rate limiter from headers
        self.rate_limiter.update_from_headers(dict(response.headers))

        if response.status_code == 429:
            # Rate limited - wait and retry
            retry_after = int(response.headers.get("Retry-After", 60))
            await asyncio.sleep(retry_after)
            raise RedditAPIError("Rate limited", 429)

        if response.status_code == 404:
            raise RedditAPIError("Not found", 404)

        if response.status_code != 200:
            raise RedditAPIError(
                f"Request failed: {response.status_code}",
                response.status_code,
            )

        return response.json()

    async def get_subreddit_about(self, subreddit: str) -> dict[str, Any]:
        """Get subreddit information.

        Args:
            subreddit: Subreddit name (without r/ prefix).

        Returns:
            Parsed subreddit information.
        """
        url = f"{self.BASE_URL}/r/{subreddit}/about.json"
        data = await self._request(url)
        return parse_subreddit_about(data)

    async def get_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 100,
        time_filter: str = "all",
    ) -> list[dict[str, Any]]:
        """Get posts from a subreddit.

        Args:
            subreddit: Subreddit name (without r/ prefix).
            sort: Sort method (hot, new, top, rising).
            limit: Maximum number of posts (max 100 per request).
            time_filter: Time filter for top posts (hour, day, week, month, year, all).

        Returns:
            List of parsed post dictionaries.
        """
        posts = []
        after = None
        remaining = limit

        while remaining > 0:
            batch_size = min(remaining, 100)
            url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json?limit={batch_size}"

            if sort == "top":
                url += f"&t={time_filter}"

            if after:
                url += f"&after={after}"

            data = await self._request(url)
            raw_posts = extract_post_listing(data)

            if not raw_posts:
                break

            posts.extend([parse_post(p) for p in raw_posts])
            remaining -= len(raw_posts)

            # Get the "after" token for pagination
            after = data.get("data", {}).get("after")
            if not after:
                break

        return posts[:limit]

    async def get_post_comments(
        self,
        subreddit: str,
        post_id: str,
        sort: str = "top",
        limit: int = 200,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Get comments for a specific post.

        Args:
            subreddit: Subreddit name.
            post_id: Reddit post ID.
            sort: Comment sort method (top, best, new, controversial).
            limit: Maximum number of comments.

        Returns:
            Tuple of (post_data, list of parsed comments).
        """
        url = (
            f"{self.BASE_URL}/r/{subreddit}/comments/{post_id}.json"
            f"?sort={sort}&limit={limit}"
        )

        data = await self._request(url)

        if not isinstance(data, list):
            return {}, []

        post_data, comments_data = extract_comments_from_post_page(data)
        comments = parse_comments_tree(comments_data, post_id)

        return parse_post(post_data), comments

    async def get_user_about(self, username: str) -> Optional[dict[str, Any]]:
        """Get user/author information.

        Args:
            username: Reddit username.

        Returns:
            Parsed author information or None if not found.
        """
        if not username or username in ("[deleted]", "AutoModerator"):
            return None

        try:
            url = f"{self.BASE_URL}/user/{username}/about.json"
            data = await self._request(url)
            return parse_author(data)
        except RedditAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_multiple_posts(
        self,
        subreddit: str,
        sort_methods: list[str] = ["hot", "top", "new"],
        limit_per_sort: int = 50,
        time_filter: str = "week",
    ) -> list[dict[str, Any]]:
        """Get posts from multiple sort methods and deduplicate.

        Args:
            subreddit: Subreddit name.
            sort_methods: List of sort methods to fetch.
            limit_per_sort: Posts to fetch per sort method.
            time_filter: Time filter for top posts.

        Returns:
            Deduplicated list of parsed posts.
        """
        all_posts = {}

        for sort in sort_methods:
            posts = await self.get_posts(
                subreddit=subreddit,
                sort=sort,
                limit=limit_per_sort,
                time_filter=time_filter,
            )
            for post in posts:
                # Use reddit_id as key for deduplication
                if post["reddit_id"] not in all_posts:
                    all_posts[post["reddit_id"]] = post

        return list(all_posts.values())

    async def get_top_posts_with_comments(
        self,
        subreddit: str,
        num_posts: int = 50,
        comments_per_post: int = 50,
        sort: str = "top",
        time_filter: str = "week",
    ) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
        """Get top posts with their comments.

        Args:
            subreddit: Subreddit name.
            num_posts: Number of posts to fetch.
            comments_per_post: Comments to fetch per post.
            sort: Post sort method.
            time_filter: Time filter for top posts.

        Returns:
            List of (post_data, comments_list) tuples.
        """
        posts = await self.get_posts(
            subreddit=subreddit,
            sort=sort,
            limit=num_posts,
            time_filter=time_filter,
        )

        results = []
        for post in posts:
            _, comments = await self.get_post_comments(
                subreddit=subreddit,
                post_id=post["reddit_id"],
                limit=comments_per_post,
            )
            results.append((post, comments))

        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Synchronous wrapper for CLI usage
class SyncRedditClient:
    """Synchronous wrapper around RedditClient for non-async contexts."""

    def __init__(self, requests_per_minute: int = 30):
        """Initialize the sync client.

        Args:
            requests_per_minute: Maximum requests per minute.
        """
        self.requests_per_minute = requests_per_minute
        self._async_client: Optional[RedditClient] = None

    def _get_or_create_client(self) -> RedditClient:
        """Get or create the async client."""
        if self._async_client is None:
            self._async_client = RedditClient(self.requests_per_minute)
        return self._async_client

    def _run(self, coro):
        """Run an async coroutine synchronously."""
        return asyncio.get_event_loop().run_until_complete(coro)

    def get_subreddit_about(self, subreddit: str) -> dict[str, Any]:
        """Get subreddit information synchronously."""
        client = self._get_or_create_client()
        return self._run(client.get_subreddit_about(subreddit))

    def get_posts(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 100,
        time_filter: str = "all",
    ) -> list[dict[str, Any]]:
        """Get posts synchronously."""
        client = self._get_or_create_client()
        return self._run(client.get_posts(subreddit, sort, limit, time_filter))

    def get_multiple_posts(
        self,
        subreddit: str,
        sort_methods: list[str] = ["hot", "top", "new"],
        limit_per_sort: int = 50,
        time_filter: str = "week",
    ) -> list[dict[str, Any]]:
        """Get posts from multiple sorts synchronously."""
        client = self._get_or_create_client()
        return self._run(
            client.get_multiple_posts(subreddit, sort_methods, limit_per_sort, time_filter)
        )

    def close(self) -> None:
        """Close the client."""
        if self._async_client:
            self._run(self._async_client.close())
            self._async_client = None
