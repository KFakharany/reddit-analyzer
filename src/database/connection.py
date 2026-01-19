"""Database connection manager for Reddit Analyzer."""

from contextlib import contextmanager
from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.database.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str | None = None):
        """Initialize the database manager.

        Args:
            database_url: Optional database URL. If not provided, uses settings.
        """
        self._database_url = database_url or get_settings().database_url
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self._database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._session_factory

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Create a context-managed database session.

        Yields:
            A SQLAlchemy session that automatically commits on success
            or rolls back on exception.
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """Get a new session (caller is responsible for closing).

        Returns:
            A new SQLAlchemy session.
        """
        return self.session_factory()

    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables in the database."""
        Base.metadata.drop_all(self.engine)

    def check_connection(self) -> bool:
        """Check if the database connection is working.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_connection_info(self) -> dict:
        """Get information about the database connection.

        Returns:
            Dictionary with connection status and details.
        """
        settings = get_settings()
        info = {
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_db,
            "user": settings.postgres_user,
            "connected": self.check_connection(),
        }

        if info["connected"]:
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    info["version"] = result.scalar()
            except Exception:
                pass

        return info

    def close(self) -> None:
        """Close the database engine and all connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


@lru_cache
def get_db_manager() -> DatabaseManager:
    """Get the cached database manager instance.

    Returns:
        The singleton DatabaseManager instance.
    """
    return DatabaseManager()
