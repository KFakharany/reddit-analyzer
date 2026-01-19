"""Repository for Community data access."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Community, CollectionRun


class CommunityRepository:
    """Data access layer for Community entities."""

    def __init__(self, session: Session):
        """Initialize with a database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def get_by_id(self, community_id: int) -> Optional[Community]:
        """Get a community by ID.

        Args:
            community_id: The community's database ID.

        Returns:
            The Community if found, None otherwise.
        """
        return self.session.get(Community, community_id)

    def get_by_name(self, name: str) -> Optional[Community]:
        """Get a community by name (case-insensitive).

        Args:
            name: The subreddit name (without r/ prefix).

        Returns:
            The Community if found, None otherwise.
        """
        stmt = select(Community).where(Community.name.ilike(name))
        return self.session.execute(stmt).scalar_one_or_none()

    def get_or_create(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        subscribers: Optional[int] = None,
    ) -> tuple[Community, bool]:
        """Get an existing community or create a new one.

        Args:
            name: The subreddit name.
            display_name: Display name (e.g., "r/PromptEngineering").
            description: Community description.
            subscribers: Number of subscribers.

        Returns:
            Tuple of (Community, created) where created is True if new.
        """
        community = self.get_by_name(name)
        if community:
            # Update with new info if provided
            if display_name:
                community.display_name = display_name
            if description:
                community.description = description
            if subscribers:
                community.subscribers = subscribers
            return community, False

        community = Community(
            name=name,
            display_name=display_name or f"r/{name}",
            description=description,
            subscribers=subscribers,
        )
        self.session.add(community)
        self.session.flush()
        return community, True

    def list_all(self) -> list[Community]:
        """Get all tracked communities.

        Returns:
            List of all Community objects.
        """
        stmt = select(Community).order_by(Community.name)
        return list(self.session.execute(stmt).scalars().all())

    def delete(self, community_id: int) -> bool:
        """Delete a community and all related data.

        Args:
            community_id: The community's database ID.

        Returns:
            True if deleted, False if not found.
        """
        community = self.get_by_id(community_id)
        if community:
            self.session.delete(community)
            return True
        return False

    def create_collection_run(self, community_id: int) -> CollectionRun:
        """Create a new collection run for a community.

        Args:
            community_id: The community's database ID.

        Returns:
            The new CollectionRun.
        """
        run = CollectionRun(community_id=community_id, status="running")
        self.session.add(run)
        self.session.flush()
        return run

    def complete_collection_run(
        self,
        run_id: int,
        posts_collected: int = 0,
        comments_collected: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[CollectionRun]:
        """Mark a collection run as completed or failed.

        Args:
            run_id: The collection run ID.
            posts_collected: Number of posts collected.
            comments_collected: Number of comments collected.
            error_message: Error message if failed.

        Returns:
            The updated CollectionRun or None if not found.
        """
        run = self.session.get(CollectionRun, run_id)
        if run:
            run.completed_at = datetime.utcnow()
            run.status = "failed" if error_message else "completed"
            run.posts_collected = posts_collected
            run.comments_collected = comments_collected
            run.error_message = error_message
        return run

    def get_collection_run(self, run_id: int) -> Optional[CollectionRun]:
        """Get a collection run by ID.

        Args:
            run_id: The collection run ID.

        Returns:
            The CollectionRun if found, None otherwise.
        """
        return self.session.get(CollectionRun, run_id)

    def get_latest_collection_run(self, community_id: int) -> Optional[CollectionRun]:
        """Get the most recent collection run for a community.

        Args:
            community_id: The community's database ID.

        Returns:
            The most recent CollectionRun or None.
        """
        stmt = (
            select(CollectionRun)
            .where(CollectionRun.community_id == community_id)
            .order_by(CollectionRun.started_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_collection_runs(
        self, community_id: int, limit: int = 10
    ) -> list[CollectionRun]:
        """List recent collection runs for a community.

        Args:
            community_id: The community's database ID.
            limit: Maximum number of runs to return.

        Returns:
            List of CollectionRun objects, most recent first.
        """
        stmt = (
            select(CollectionRun)
            .where(CollectionRun.community_id == community_id)
            .order_by(CollectionRun.started_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
