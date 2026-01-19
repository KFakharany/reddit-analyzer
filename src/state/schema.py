"""LangGraph state schemas for Reddit Analyzer workflows."""

from typing import Any, Optional, TypedDict

from src.state.enums import AnalysisPhase, WorkflowStatus


class CommunityInfo(TypedDict, total=False):
    """Information about a subreddit."""

    name: str
    display_name: str
    description: str
    subscribers: int
    community_id: int


class CollectionConfig(TypedDict, total=False):
    """Configuration for data collection."""

    posts_limit: int
    comments_limit: int
    sort_methods: list[str]
    time_filter: str
    fetch_authors: bool


class CollectionState(TypedDict, total=False):
    """State for the collection subgraph."""

    # Input
    community_name: str
    config: CollectionConfig

    # Progress
    posts_fetched: int
    comments_fetched: int
    authors_fetched: int

    # Raw data (temporary, not persisted)
    raw_posts: list[dict[str, Any]]
    raw_comments: list[dict[str, Any]]
    raw_authors: list[dict[str, Any]]

    # Output
    collection_run_id: int
    community_id: int


class ExtractionResults(TypedDict, total=False):
    """Results from pattern extraction."""

    score_distribution: dict[str, Any]
    flair_distribution: dict[str, int]
    timing_patterns: dict[str, Any]
    title_analysis: dict[str, Any]
    op_engagement_analysis: dict[str, Any]
    upvote_ratio_analysis: dict[str, Any]
    post_format_analysis: dict[str, Any]
    author_success_analysis: dict[str, Any]
    audience_extraction: dict[str, Any]


class AIAnalysisResults(TypedDict, total=False):
    """Results from AI-powered analysis."""

    sentiment_analysis: dict[str, Any]
    pain_point_analysis: dict[str, Any]
    tone_analysis: dict[str, Any]
    promotion_analysis: dict[str, Any]


class SynthesisResults(TypedDict, total=False):
    """Results from AI-powered synthesis."""

    personas: list[dict[str, Any]]
    insights: list[dict[str, Any]]
    report_content: str


class AnalysisState(TypedDict, total=False):
    """State for analysis and synthesis subgraphs."""

    # Input
    collection_run_id: int
    community_id: int
    community_info: CommunityInfo

    # Data for analysis
    posts: list[dict[str, Any]]
    comments: list[dict[str, Any]]
    top_posts: list[dict[str, Any]]
    top_comments: list[dict[str, Any]]

    # Extraction results
    extraction_results: ExtractionResults

    # AI analysis results
    ai_analysis: AIAnalysisResults

    # Synthesis results
    synthesis: SynthesisResults


class WorkflowState(TypedDict, total=False):
    """Main workflow state for LangGraph."""

    # Workflow identity
    workflow_id: str
    status: WorkflowStatus
    phase: AnalysisPhase

    # Input configuration
    community_name: str
    skip_collection: bool
    skip_ai: bool
    existing_run_id: Optional[int]
    output_dir: str

    # Collection config
    collection_config: CollectionConfig

    # Community info
    community_info: CommunityInfo
    community_id: int

    # Collection results
    collection_run_id: int
    posts_collected: int
    comments_collected: int

    # Analysis data
    posts: list[dict[str, Any]]
    comments: list[dict[str, Any]]
    top_posts: list[dict[str, Any]]
    top_comments: list[dict[str, Any]]

    # Extraction results
    extraction_results: ExtractionResults

    # AI analysis results
    ai_analysis: AIAnalysisResults

    # Synthesis results
    synthesis: SynthesisResults

    # Output
    report_path: Optional[str]

    # Error handling
    error: Optional[str]
    errors: list[str]


# Reducer functions for LangGraph state updates
def merge_dicts(
    existing: dict[str, Any] | None,
    new: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge two dictionaries, with new values taking precedence.

    Args:
        existing: Existing dictionary.
        new: New values to merge.

    Returns:
        Merged dictionary.
    """
    if existing is None:
        return new or {}
    if new is None:
        return existing
    return {**existing, **new}


def append_errors(
    existing: list[str] | None,
    new: list[str] | str | None,
) -> list[str]:
    """Append errors to the error list.

    Args:
        existing: Existing error list.
        new: New error(s) to append.

    Returns:
        Updated error list.
    """
    result = list(existing) if existing else []
    if new:
        if isinstance(new, str):
            result.append(new)
        else:
            result.extend(new)
    return result


# Default configuration
DEFAULT_COLLECTION_CONFIG: CollectionConfig = {
    "posts_limit": 100,
    "comments_limit": 50,
    "sort_methods": ["hot", "top", "new"],
    "time_filter": "week",
    "fetch_authors": False,
}


def create_initial_state(
    community_name: str,
    skip_ai: bool = False,
    skip_collection: bool = False,
    existing_run_id: Optional[int] = None,
    output_dir: str = "./output",
    **config_overrides,
) -> WorkflowState:
    """Create an initial workflow state.

    Args:
        community_name: Name of the subreddit to analyze.
        skip_ai: Skip AI analysis steps.
        skip_collection: Skip data collection (use existing data).
        existing_run_id: Existing collection run to analyze.
        output_dir: Directory for output files.
        **config_overrides: Override default collection config.

    Returns:
        Initial WorkflowState.
    """
    config = {**DEFAULT_COLLECTION_CONFIG}
    for key in config_overrides:
        if key in config:
            config[key] = config_overrides[key]

    return WorkflowState(
        status=WorkflowStatus.PENDING,
        phase=AnalysisPhase.INIT,
        community_name=community_name,
        skip_collection=skip_collection,
        skip_ai=skip_ai,
        existing_run_id=existing_run_id,
        output_dir=output_dir,
        collection_config=config,
        posts=[],
        comments=[],
        top_posts=[],
        top_comments=[],
        extraction_results={},
        ai_analysis={},
        synthesis={},
        errors=[],
    )
