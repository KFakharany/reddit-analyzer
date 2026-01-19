"""Node for fetching comments from Reddit."""

import asyncio
from typing import Any

from src.reddit import RedditClient
from src.state import WorkflowState


async def _fetch_comments_async(
    community_name: str,
    posts: list[dict[str, Any]],
    comments_per_post: int,
) -> list[dict[str, Any]]:
    """Async implementation of comment fetching.

    Args:
        community_name: Subreddit name.
        posts: List of posts to fetch comments for.
        comments_per_post: Number of comments per post.

    Returns:
        List of all comments with post_reddit_id added.
    """
    all_comments = []

    async with RedditClient() as client:
        for post in posts:
            post_id = post.get("reddit_id")
            if not post_id:
                continue

            try:
                _, comments = await client.get_post_comments(
                    subreddit=community_name,
                    post_id=post_id,
                    limit=comments_per_post,
                )

                # Add post reference to each comment
                for comment in comments:
                    comment["post_reddit_id"] = post_id

                all_comments.extend(comments)

            except Exception:
                # Skip posts that fail, continue with others
                continue

    return all_comments


def fetch_comments_node(state: WorkflowState) -> dict[str, Any]:
    """Fetch comments for the top posts.

    This is a SCRIPT node - no AI involved.
    Fetches comments for the top N posts to analyze discussions.

    Args:
        state: Current workflow state.

    Returns:
        State update with fetched comments.
    """
    community_name = state["community_name"]
    config = state.get("collection_config", {})
    top_posts = state.get("top_posts", [])

    if not top_posts:
        return {
            "comments": [],
            "top_comments": [],
            "comments_collected": 0,
        }

    comments_limit = config.get("comments_limit", 50)

    try:
        # Run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            comments = loop.run_until_complete(
                _fetch_comments_async(
                    community_name=community_name,
                    posts=top_posts,
                    comments_per_post=comments_limit,
                )
            )
        finally:
            loop.close()

        # Sort by score
        comments = sorted(comments, key=lambda c: c.get("score", 0), reverse=True)

        # Identify top comments for detailed analysis
        top_comments = comments[:min(50, len(comments))]

        return {
            "comments": comments,
            "top_comments": top_comments,
            "comments_collected": len(comments),
        }

    except Exception as e:
        return {
            "error": f"Failed to fetch comments: {str(e)}",
            "errors": [f"Comment fetch error: {str(e)}"],
            "comments": [],
            "top_comments": [],
            "comments_collected": 0,
        }
