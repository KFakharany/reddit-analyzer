"""SQLAlchemy ORM models for Reddit Analyzer."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Community(Base):
    """Communities being tracked."""

    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    subscribers: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    collection_runs: Mapped[list["CollectionRun"]] = relationship(
        back_populates="community", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="community", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Community(name='{self.name}', subscribers={self.subscribers})>"


class CollectionRun(Base):
    """Each data collection run for time-series tracking."""

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="running")
    posts_collected: Mapped[int] = mapped_column(Integer, default=0)
    comments_collected: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    community: Mapped["Community"] = relationship(back_populates="collection_runs")
    posts: Mapped[list["Post"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan"
    )
    analysis_result: Mapped[Optional["AnalysisResult"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan", uselist=False
    )
    audience_analysis: Mapped[Optional["AudienceAnalysis"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan", uselist=False
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_collection_runs_community", "community_id"),)

    def __repr__(self) -> str:
        return f"<CollectionRun(id={self.id}, status='{self.status}')>"


class Post(Base):
    """Reddit posts with versioning per collection run."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reddit_id: Mapped[str] = mapped_column(String(20), nullable=False)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="CASCADE")
    )
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    selftext: Mapped[Optional[str]] = mapped_column(Text)
    author_name: Mapped[Optional[str]] = mapped_column(String(50))
    score: Mapped[Optional[int]] = mapped_column(Integer)
    upvote_ratio: Mapped[Optional[float]] = mapped_column(Float)
    num_comments: Mapped[Optional[int]] = mapped_column(Integer)
    flair_text: Mapped[Optional[str]] = mapped_column(String(100))
    is_self: Mapped[bool] = mapped_column(Boolean, default=True)
    is_video: Mapped[bool] = mapped_column(Boolean, default=False)
    permalink: Mapped[Optional[str]] = mapped_column(String(500))
    created_utc: Mapped[Optional[datetime]] = mapped_column()
    collected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="posts")
    community: Mapped["Community"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("reddit_id", "collection_run_id", name="uq_post_reddit_collection"),
        Index("idx_posts_community", "community_id"),
        Index("idx_posts_collection", "collection_run_id"),
        Index("idx_posts_created", "created_utc"),
        Index("idx_posts_score", "score"),
    )

    def __repr__(self) -> str:
        return f"<Post(reddit_id='{self.reddit_id}', score={self.score})>"


class Comment(Base):
    """Reddit comments with threading support."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reddit_id: Mapped[str] = mapped_column(String(20), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="CASCADE")
    )
    parent_reddit_id: Mapped[Optional[str]] = mapped_column(String(20))
    author_name: Mapped[Optional[str]] = mapped_column(String(50))
    body: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[Optional[int]] = mapped_column(Integer)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    is_submitter: Mapped[bool] = mapped_column(Boolean, default=False)
    created_utc: Mapped[Optional[datetime]] = mapped_column()
    collected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    post: Mapped["Post"] = relationship(back_populates="comments")
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="comments")

    __table_args__ = (
        Index("idx_comments_post", "post_id"),
        Index("idx_comments_collection", "collection_run_id"),
        Index("idx_comments_score", "score"),
    )

    def __repr__(self) -> str:
        return f"<Comment(reddit_id='{self.reddit_id}', score={self.score})>"


class Author(Base):
    """Reddit author profiles."""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    link_karma: Mapped[Optional[int]] = mapped_column(Integer)
    comment_karma: Mapped[Optional[int]] = mapped_column(Integer)
    total_karma: Mapped[Optional[int]] = mapped_column(Integer)
    account_created_utc: Mapped[Optional[datetime]] = mapped_column()
    is_gold: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Author(username='{self.username}', total_karma={self.total_karma})>"


class AnalysisResult(Base):
    """Analysis results for a collection run."""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="CASCADE"), unique=True
    )

    # Basic stats (JSON for flexibility)
    score_distribution: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    flair_distribution: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    timing_patterns: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Enhanced analysis
    title_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    op_engagement_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    upvote_ratio_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    post_format_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    author_success_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # AI-generated analysis
    sentiment_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    pain_point_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    tone_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    promotion_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="analysis_result")

    def __repr__(self) -> str:
        return f"<AnalysisResult(collection_run_id={self.collection_run_id})>"


class AudienceAnalysis(Base):
    """Audience analysis for a collection run."""

    __tablename__ = "audience_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="CASCADE"), unique=True
    )

    self_identifications: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    skill_levels: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    goals_motivations: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    pain_points: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    tools_mentioned: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    budget_signals: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    skepticism_level: Mapped[Optional[str]] = mapped_column(String(20))
    personas: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="audience_analysis")

    def __repr__(self) -> str:
        return f"<AudienceAnalysis(collection_run_id={self.collection_run_id})>"


class Report(Base):
    """Generated reports."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="CASCADE")
    )
    report_type: Mapped[Optional[str]] = mapped_column(String(50))
    content: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type='{self.report_type}')>"
