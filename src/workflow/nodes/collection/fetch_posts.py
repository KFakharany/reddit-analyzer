"""Node for fetching posts from Reddit."""

import asyncio
from typing import Any

from src.reddit import RedditClient
from src.state import WorkflowState, AnalysisPhase


async def _fetch_posts_async(
    community_name: str,
    sort_methods: list[str],
    limit_per_sort: int,
    time_filter: str,
) -> list[dict[str, Any]]:
    """Async implementation of post fetching.

    Args:
        community_name: Subreddit name.
        sort_methods: List of sort methods to use.
        limit_per_sort: Posts per sort method.
        time_filter: Time filter for top posts.

    Returns:
        List of deduplicated posts.
    """
    async with RedditClient() as client:
        posts = await client.get_multiple_posts(
            subreddit=community_name,
            sort_methods=sort_methods,
            limit_per_sort=limit_per_sort,
            time_filter=time_filter,
        )
        return posts


def fetch_posts_node(state: WorkflowState) -> dict[str, Any]:
    """Fetch posts from Reddit for the specified community.

    This is a SCRIPT node - no AI involved.
    Fetches posts from multiple sort methods and deduplicates.

    Args:
        state: Current workflow state.

    Returns:
        State update with fetched posts.
    """
    community_name = state["community_name"]
    config = state.get("collection_config", {})

    sort_methods = config.get("sort_methods", ["hot", "top", "new"])
    posts_limit = config.get("posts_limit", 100)
    time_filter = config.get("time_filter", "week")

    # Calculate limit per sort to roughly achieve total desired
    limit_per_sort = max(posts_limit // len(sort_methods), 25)

    try:
        # Run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            posts = loop.run_until_complete(
                _fetch_posts_async(
                    community_name=community_name,
                    sort_methods=sort_methods,
                    limit_per_sort=limit_per_sort,
                    time_filter=time_filter,
                )
            )
        finally:
            loop.close()

        # Sort by score and take top N
        posts = sorted(posts, key=lambda p: p.get("score", 0), reverse=True)
        posts = posts[:posts_limit]

        # Identify top posts for detailed analysis
        top_posts = posts[:min(20, len(posts))]

        return {
            "phase": AnalysisPhase.COLLECTING,
            "posts": posts,
            "top_posts": top_posts,
            "posts_collected": len(posts),
        }

    except Exception as e:
        return {
            "error": f"Failed to fetch posts: {str(e)}",
            "errors": [f"Post fetch error: {str(e)}"],
        }
