"""Node for storing collected data to database."""

from datetime import datetime
from typing import Any

from src.database import get_db_manager
from src.database.repositories import CommunityRepository, PostRepository, CommentRepository
from src.reddit import RedditClient
from src.state import WorkflowState
import asyncio


async def _get_subreddit_info(community_name: str) -> dict[str, Any]:
    """Fetch subreddit info asynchronously."""
    async with RedditClient() as client:
        return await client.get_subreddit_about(community_name)


def store_to_db_node(state: WorkflowState) -> dict[str, Any]:
    """Store collected posts and comments to the database.

    This is a SCRIPT node - no AI involved.
    Creates community record, collection run, and stores all data.

    Args:
        state: Current workflow state.

    Returns:
        State update with database IDs.
    """
    community_name = state["community_name"]
    posts = state.get("posts", [])
    comments = state.get("comments", [])

    db = get_db_manager()

    try:
        with db.session() as session:
            community_repo = CommunityRepository(session)
            post_repo = PostRepository(session)
            comment_repo = CommentRepository(session)

            # Get or create community
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    subreddit_info = loop.run_until_complete(
                        _get_subreddit_info(community_name)
                    )
                finally:
                    loop.close()
            except Exception:
                subreddit_info = {"name": community_name}

            community, _ = community_repo.get_or_create(
                name=community_name,
                display_name=subreddit_info.get("display_name"),
                description=subreddit_info.get("description"),
                subscribers=subreddit_info.get("subscribers"),
            )

            # Create collection run
            collection_run = community_repo.create_collection_run(community.id)

            # Store posts
            post_id_map = {}  # reddit_id -> db_id
            for post_data in posts:
                post = post_repo.create(
                    reddit_id=post_data["reddit_id"],
                    collection_run_id=collection_run.id,
                    community_id=community.id,
                    title=post_data["title"],
                    selftext=post_data.get("selftext"),
                    author_name=post_data.get("author_name"),
                    score=post_data.get("score"),
                    upvote_ratio=post_data.get("upvote_ratio"),
                    num_comments=post_data.get("num_comments"),
                    flair_text=post_data.get("flair_text"),
                    is_self=post_data.get("is_self", True),
                    is_video=post_data.get("is_video", False),
                    permalink=post_data.get("permalink"),
                    created_utc=post_data.get("created_utc"),
                )
                post_id_map[post_data["reddit_id"]] = post.id

            # Store comments
            for comment_data in comments:
                post_reddit_id = comment_data.get("post_reddit_id")
                post_db_id = post_id_map.get(post_reddit_id)

                if post_db_id:
                    comment_repo.create(
                        reddit_id=comment_data["reddit_id"],
                        post_id=post_db_id,
                        collection_run_id=collection_run.id,
                        parent_reddit_id=comment_data.get("parent_reddit_id"),
                        author_name=comment_data.get("author_name"),
                        body=comment_data.get("body"),
                        score=comment_data.get("score"),
                        depth=comment_data.get("depth", 0),
                        is_submitter=comment_data.get("is_submitter", False),
                        created_utc=comment_data.get("created_utc"),
                    )

            # Update collection run status
            community_repo.complete_collection_run(
                run_id=collection_run.id,
                posts_collected=len(posts),
                comments_collected=len(comments),
            )

            return {
                "community_id": community.id,
                "collection_run_id": collection_run.id,
                "community_info": {
                    "name": community.name,
                    "display_name": community.display_name,
                    "description": community.description,
                    "subscribers": community.subscribers,
                    "community_id": community.id,
                },
            }

    except Exception as e:
        return {
            "error": f"Failed to store data: {str(e)}",
            "errors": [f"Database store error: {str(e)}"],
        }
