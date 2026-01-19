"""Workflow nodes for Reddit Analyzer."""

from .collection import (
    fetch_posts_node,
    fetch_comments_node,
    store_to_db_node,
)
from .extraction import (
    extract_scores_node,
    extract_flairs_node,
    extract_timing_node,
    extract_titles_node,
    extract_engagement_node,
    extract_audience_node,
    merge_extraction_node,
)
from .analysis import (
    analyze_sentiment_node,
    analyze_pain_points_node,
    analyze_tone_node,
    analyze_promotion_node,
    merge_analysis_node,
)
from .synthesis import (
    generate_personas_node,
    generate_insights_node,
    generate_report_node,
)

__all__ = [
    # Collection
    "fetch_posts_node",
    "fetch_comments_node",
    "store_to_db_node",
    # Extraction
    "extract_scores_node",
    "extract_flairs_node",
    "extract_timing_node",
    "extract_titles_node",
    "extract_engagement_node",
    "extract_audience_node",
    "merge_extraction_node",
    # Analysis
    "analyze_sentiment_node",
    "analyze_pain_points_node",
    "analyze_tone_node",
    "analyze_promotion_node",
    "merge_analysis_node",
    # Synthesis
    "generate_personas_node",
    "generate_insights_node",
    "generate_report_node",
]
