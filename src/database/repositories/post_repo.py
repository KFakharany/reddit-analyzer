"""Repository for Post data access."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models import Post


class PostRepository:
    """Data access layer for Post entities."""

    def __init__(self, session: Session):
        """Initialize with a database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get a post by ID.

        Args:
            post_id: The post's database ID.

        Returns:
            The Post if found, None otherwise.
        """
        return self.session.get(Post, post_id)

    def get_by_reddit_id(
        self, reddit_id: str, collection_run_id: int
    ) -> Optional[Post]:
        """Get a post by Reddit ID within a collection run.

        Args:
            reddit_id: Reddit's post ID.
            collection_run_id: The collection run ID.

        Returns:
            The Post if found, None otherwise.
        """
        stmt = select(Post).where(
            Post.reddit_id == reddit_id,
            Post.collection_run_id == collection_run_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        reddit_id: str,
        collection_run_id: int,
        community_id: int,
        title: str,
        selftext: Optional[str] = None,
        author_name: Optional[str] = None,
        score: Optional[int] = None,
        upvote_ratio: Optional[float] = None,
        num_comments: Optional[int] = None,
        flair_text: Optional[str] = None,
        is_self: bool = True,
        is_video: bool = False,
        permalink: Optional[str] = None,
        created_utc: Optional[datetime] = None,
    ) -> Post:
        """Create a new post.

        Args:
            reddit_id: Reddit's post ID.
            collection_run_id: The collection run ID.
            community_id: The community ID.
            title: Post title.
            selftext: Post body text.
            author_name: Author's username.
            score: Post score.
            upvote_ratio: Upvote ratio (0-1).
            num_comments: Number of comments.
            flair_text: Post flair text.
            is_self: Is this a self/text post.
            is_video: Is this a video post.
            permalink: Reddit permalink.
            created_utc: When the post was created.

        Returns:
            The new Post.
        """
        post = Post(
            reddit_id=reddit_id,
            collection_run_id=collection_run_id,
            community_id=community_id,
            title=title,
            selftext=selftext,
            author_name=author_name,
            score=score,
            upvote_ratio=upvote_ratio,
            num_comments=num_comments,
            flair_text=flair_text,
            is_self=is_self,
            is_video=is_video,
            permalink=permalink,
            created_utc=created_utc,
        )
        self.session.add(post)
        self.session.flush()
        return post

    def bulk_create(self, posts_data: list[dict[str, Any]]) -> list[Post]:
        """Bulk create posts.

        Args:
            posts_data: List of dictionaries with post data.

        Returns:
            List of created Post objects.
        """
        posts = [Post(**data) for data in posts_data]
        self.session.add_all(posts)
        self.session.flush()
        return posts

    def get_by_collection_run(
        self,
        collection_run_id: int,
        limit: Optional[int] = None,
        order_by_score: bool = True,
    ) -> list[Post]:
        """Get posts for a collection run.

        Args:
            collection_run_id: The collection run ID.
            limit: Maximum number of posts to return.
            order_by_score: Sort by score descending.

        Returns:
            List of Post objects.
        """
        stmt = select(Post).where(Post.collection_run_id == collection_run_id)

        if order_by_score:
            stmt = stmt.order_by(Post.score.desc())

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def get_by_community(
        self,
        community_id: int,
        limit: Optional[int] = None,
        order_by_score: bool = True,
    ) -> list[Post]:
        """Get posts for a community across all collection runs.

        Args:
            community_id: The community ID.
            limit: Maximum number of posts to return.
            order_by_score: Sort by score descending.

        Returns:
            List of Post objects.
        """
        stmt = select(Post).where(Post.community_id == community_id)

        if order_by_score:
            stmt = stmt.order_by(Post.score.desc())

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def count_by_collection_run(self, collection_run_id: int) -> int:
        """Count posts in a collection run.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            Number of posts.
        """
        stmt = (
            select(func.count())
            .select_from(Post)
            .where(Post.collection_run_id == collection_run_id)
        )
        return self.session.execute(stmt).scalar() or 0

    def get_score_distribution(
        self, collection_run_id: int
    ) -> dict[str, Any]:
        """Get score distribution statistics for posts.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            Dictionary with min, max, avg, median, and buckets.
        """
        posts = self.get_by_collection_run(collection_run_id, order_by_score=True)
        if not posts:
            return {"min": 0, "max": 0, "avg": 0, "total": 0, "buckets": {}}

        scores = [p.score or 0 for p in posts]
        sorted_scores = sorted(scores)

        # Define score buckets
        buckets = {
            "0-10": 0,
            "11-50": 0,
            "51-100": 0,
            "101-500": 0,
            "501-1000": 0,
            "1000+": 0,
        }

        for score in scores:
            if score <= 10:
                buckets["0-10"] += 1
            elif score <= 50:
                buckets["11-50"] += 1
            elif score <= 100:
                buckets["51-100"] += 1
            elif score <= 500:
                buckets["101-500"] += 1
            elif score <= 1000:
                buckets["501-1000"] += 1
            else:
                buckets["1000+"] += 1

        n = len(sorted_scores)
        median = sorted_scores[n // 2] if n % 2 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2

        return {
            "min": min(scores),
            "max": max(scores),
            "avg": round(sum(scores) / len(scores), 2),
            "median": median,
            "total": len(scores),
            "buckets": buckets,
        }

    def get_flair_distribution(self, collection_run_id: int) -> dict[str, int]:
        """Get flair distribution for posts.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            Dictionary mapping flair text to count.
        """
        stmt = (
            select(Post.flair_text, func.count().label("count"))
            .where(Post.collection_run_id == collection_run_id)
            .group_by(Post.flair_text)
            .order_by(func.count().desc())
        )
        results = self.session.execute(stmt).all()
        return {flair or "No Flair": count for flair, count in results}

    def get_top_authors(
        self, collection_run_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get top authors by total post score.

        Args:
            collection_run_id: The collection run ID.
            limit: Maximum number of authors to return.

        Returns:
            List of dicts with author name and stats.
        """
        stmt = (
            select(
                Post.author_name,
                func.count().label("post_count"),
                func.sum(Post.score).label("total_score"),
                func.avg(Post.score).label("avg_score"),
            )
            .where(
                Post.collection_run_id == collection_run_id,
                Post.author_name.isnot(None),
                Post.author_name != "[deleted]",
            )
            .group_by(Post.author_name)
            .order_by(func.sum(Post.score).desc())
            .limit(limit)
        )
        results = self.session.execute(stmt).all()
        return [
            {
                "author": author,
                "post_count": count,
                "total_score": total,
                "avg_score": round(float(avg), 2),
            }
            for author, count, total, avg in results
        ]
