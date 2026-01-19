"""Enums for Reddit Analyzer state and data models."""

from enum import Enum


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisPhase(str, Enum):
    """Current phase of the analysis workflow."""

    INIT = "init"
    COLLECTING = "collecting"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    OUTPUTTING = "outputting"
    DONE = "done"


class SkillLevel(str, Enum):
    """Skill/experience level of community members."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MIXED = "mixed"


class SentimentType(str, Enum):
    """Types of sentiment in content."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class SkepticismLevel(str, Enum):
    """Level of skepticism in a community."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ContentTone(str, Enum):
    """Tone of community content."""

    CASUAL = "casual"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    MIXED = "mixed"


class PromotionReception(str, Enum):
    """How promotional content is received."""

    WELCOMED = "welcomed"
    TOLERATED = "tolerated"
    SKEPTICAL = "skeptical"
    HOSTILE = "hostile"


class PostType(str, Enum):
    """Types of Reddit posts."""

    QUESTION = "question"
    DISCUSSION = "discussion"
    SHOWCASE = "showcase"
    TUTORIAL = "tutorial"
    NEWS = "news"
    RESOURCE = "resource"
    HELP_REQUEST = "help_request"
    OTHER = "other"


class EngagementLevel(str, Enum):
    """Level of engagement for posts."""

    VIRAL = "viral"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"
