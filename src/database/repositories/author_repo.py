"""Repository for Author data access."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Author


class AuthorRepository:
    """Data access layer for Author entities."""

    def __init__(self, session: Session):
        """Initialize with a database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def get_by_id(self, author_id: int) -> Optional[Author]:
        """Get an author by ID.

        Args:
            author_id: The author's database ID.

        Returns:
            The Author if found, None otherwise.
        """
        return self.session.get(Author, author_id)

    def get_by_username(self, username: str) -> Optional[Author]:
        """Get an author by username.

        Args:
            username: Reddit username.

        Returns:
            The Author if found, None otherwise.
        """
        stmt = select(Author).where(Author.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        username: str,
        link_karma: Optional[int] = None,
        comment_karma: Optional[int] = None,
        total_karma: Optional[int] = None,
        account_created_utc: Optional[datetime] = None,
        is_gold: bool = False,
    ) -> Author:
        """Create a new author.

        Args:
            username: Reddit username.
            link_karma: Post karma.
            comment_karma: Comment karma.
            total_karma: Total karma.
            account_created_utc: Account creation date.
            is_gold: Has Reddit Gold/Premium.

        Returns:
            The new Author.
        """
        author = Author(
            username=username,
            link_karma=link_karma,
            comment_karma=comment_karma,
            total_karma=total_karma,
            account_created_utc=account_created_utc,
            is_gold=is_gold,
        )
        self.session.add(author)
        self.session.flush()
        return author

    def get_or_create(
        self,
        username: str,
        link_karma: Optional[int] = None,
        comment_karma: Optional[int] = None,
        total_karma: Optional[int] = None,
        account_created_utc: Optional[datetime] = None,
        is_gold: bool = False,
    ) -> tuple[Author, bool]:
        """Get an existing author or create a new one.

        Args:
            username: Reddit username.
            link_karma: Post karma.
            comment_karma: Comment karma.
            total_karma: Total karma.
            account_created_utc: Account creation date.
            is_gold: Has Reddit Gold/Premium.

        Returns:
            Tuple of (Author, created) where created is True if new.
        """
        author = self.get_by_username(username)
        if author:
            # Update with new info
            if link_karma is not None:
                author.link_karma = link_karma
            if comment_karma is not None:
                author.comment_karma = comment_karma
            if total_karma is not None:
                author.total_karma = total_karma
            if account_created_utc is not None:
                author.account_created_utc = account_created_utc
            if is_gold:
                author.is_gold = is_gold
            author.fetched_at = datetime.utcnow()
            return author, False

        author = self.create(
            username=username,
            link_karma=link_karma,
            comment_karma=comment_karma,
            total_karma=total_karma,
            account_created_utc=account_created_utc,
            is_gold=is_gold,
        )
        return author, True

    def bulk_create(self, authors_data: list[dict[str, Any]]) -> list[Author]:
        """Bulk create authors (skips existing).

        Args:
            authors_data: List of dictionaries with author data.

        Returns:
            List of created Author objects.
        """
        created = []
        for data in authors_data:
            username = data.get("username")
            if username:
                existing = self.get_by_username(username)
                if not existing:
                    author = Author(**data)
                    self.session.add(author)
                    created.append(author)
        self.session.flush()
        return created

    def list_all(self, limit: Optional[int] = None) -> list[Author]:
        """Get all authors.

        Args:
            limit: Maximum number of authors to return.

        Returns:
            List of Author objects.
        """
        stmt = select(Author).order_by(Author.total_karma.desc())
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_karma_range(
        self, min_karma: int = 0, max_karma: Optional[int] = None
    ) -> list[Author]:
        """Get authors within a karma range.

        Args:
            min_karma: Minimum total karma.
            max_karma: Maximum total karma (optional).

        Returns:
            List of Author objects.
        """
        stmt = select(Author).where(Author.total_karma >= min_karma)
        if max_karma is not None:
            stmt = stmt.where(Author.total_karma <= max_karma)
        stmt = stmt.order_by(Author.total_karma.desc())
        return list(self.session.execute(stmt).scalars().all())
