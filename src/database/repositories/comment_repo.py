"""Repository for Comment data access."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models import Comment, Post


class CommentRepository:
    """Data access layer for Comment entities."""

    def __init__(self, session: Session):
        """Initialize with a database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get a comment by ID.

        Args:
            comment_id: The comment's database ID.

        Returns:
            The Comment if found, None otherwise.
        """
        return self.session.get(Comment, comment_id)

    def create(
        self,
        reddit_id: str,
        post_id: int,
        collection_run_id: int,
        parent_reddit_id: Optional[str] = None,
        author_name: Optional[str] = None,
        body: Optional[str] = None,
        score: Optional[int] = None,
        depth: int = 0,
        is_submitter: bool = False,
        created_utc: Optional[datetime] = None,
    ) -> Comment:
        """Create a new comment.

        Args:
            reddit_id: Reddit's comment ID.
            post_id: The parent post's database ID.
            collection_run_id: The collection run ID.
            parent_reddit_id: Reddit ID of parent comment (for threading).
            author_name: Author's username.
            body: Comment body text.
            score: Comment score.
            depth: Nesting depth in thread.
            is_submitter: Is this the post's OP.
            created_utc: When the comment was created.

        Returns:
            The new Comment.
        """
        comment = Comment(
            reddit_id=reddit_id,
            post_id=post_id,
            collection_run_id=collection_run_id,
            parent_reddit_id=parent_reddit_id,
            author_name=author_name,
            body=body,
            score=score,
            depth=depth,
            is_submitter=is_submitter,
            created_utc=created_utc,
        )
        self.session.add(comment)
        self.session.flush()
        return comment

    def bulk_create(self, comments_data: list[dict[str, Any]]) -> list[Comment]:
        """Bulk create comments.

        Args:
            comments_data: List of dictionaries with comment data.

        Returns:
            List of created Comment objects.
        """
        comments = [Comment(**data) for data in comments_data]
        self.session.add_all(comments)
        self.session.flush()
        return comments

    def get_by_post(
        self,
        post_id: int,
        limit: Optional[int] = None,
        order_by_score: bool = True,
    ) -> list[Comment]:
        """Get comments for a post.

        Args:
            post_id: The post's database ID.
            limit: Maximum number of comments to return.
            order_by_score: Sort by score descending.

        Returns:
            List of Comment objects.
        """
        stmt = select(Comment).where(Comment.post_id == post_id)

        if order_by_score:
            stmt = stmt.order_by(Comment.score.desc())

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def get_by_collection_run(
        self,
        collection_run_id: int,
        limit: Optional[int] = None,
        order_by_score: bool = True,
    ) -> list[Comment]:
        """Get comments for a collection run.

        Args:
            collection_run_id: The collection run ID.
            limit: Maximum number of comments to return.
            order_by_score: Sort by score descending.

        Returns:
            List of Comment objects.
        """
        stmt = select(Comment).where(Comment.collection_run_id == collection_run_id)

        if order_by_score:
            stmt = stmt.order_by(Comment.score.desc())

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def count_by_collection_run(self, collection_run_id: int) -> int:
        """Count comments in a collection run.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            Number of comments.
        """
        stmt = (
            select(func.count())
            .select_from(Comment)
            .where(Comment.collection_run_id == collection_run_id)
        )
        return self.session.execute(stmt).scalar() or 0

    def get_op_comments(self, collection_run_id: int) -> list[Comment]:
        """Get all OP (original poster) comments.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            List of Comment objects from OPs.
        """
        stmt = (
            select(Comment)
            .where(
                Comment.collection_run_id == collection_run_id,
                Comment.is_submitter == True,
            )
            .order_by(Comment.score.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_op_engagement_stats(self, collection_run_id: int) -> dict[str, Any]:
        """Get statistics about OP engagement in comments.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            Dictionary with OP engagement statistics.
        """
        # Count total posts
        total_posts_stmt = (
            select(func.count(func.distinct(Comment.post_id)))
            .where(Comment.collection_run_id == collection_run_id)
        )
        total_posts = self.session.execute(total_posts_stmt).scalar() or 0

        # Count posts where OP replied
        posts_with_op_stmt = (
            select(func.count(func.distinct(Comment.post_id)))
            .where(
                Comment.collection_run_id == collection_run_id,
                Comment.is_submitter == True,
            )
        )
        posts_with_op = self.session.execute(posts_with_op_stmt).scalar() or 0

        # Get OP comment stats
        op_stats_stmt = (
            select(
                func.count().label("total_op_comments"),
                func.avg(Comment.score).label("avg_op_score"),
            )
            .where(
                Comment.collection_run_id == collection_run_id,
                Comment.is_submitter == True,
            )
        )
        result = self.session.execute(op_stats_stmt).one()

        return {
            "total_posts_with_comments": total_posts,
            "posts_with_op_replies": posts_with_op,
            "op_engagement_rate": round(posts_with_op / total_posts * 100, 2) if total_posts > 0 else 0,
            "total_op_comments": result.total_op_comments or 0,
            "avg_op_comment_score": round(float(result.avg_op_score or 0), 2),
        }

    def get_top_commenters(
        self, collection_run_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get top commenters by total comment score.

        Args:
            collection_run_id: The collection run ID.
            limit: Maximum number of authors to return.

        Returns:
            List of dicts with author name and stats.
        """
        stmt = (
            select(
                Comment.author_name,
                func.count().label("comment_count"),
                func.sum(Comment.score).label("total_score"),
                func.avg(Comment.score).label("avg_score"),
            )
            .where(
                Comment.collection_run_id == collection_run_id,
                Comment.author_name.isnot(None),
                Comment.author_name != "[deleted]",
            )
            .group_by(Comment.author_name)
            .order_by(func.sum(Comment.score).desc())
            .limit(limit)
        )
        results = self.session.execute(stmt).all()
        return [
            {
                "author": author,
                "comment_count": count,
                "total_score": total,
                "avg_score": round(float(avg), 2),
            }
            for author, count, total, avg in results
        ]
