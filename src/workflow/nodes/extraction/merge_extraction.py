"""Node for merging all extraction results."""

from typing import Any

from src.state import WorkflowState, AnalysisPhase


def merge_extraction_node(state: WorkflowState) -> dict[str, Any]:
    """Merge all extraction results into a single dictionary.

    This is a SCRIPT node - no AI involved.
    Combines all extraction results and transitions to analysis phase.

    Args:
        state: Current workflow state.

    Returns:
        State update with merged extraction results.
    """
    extraction_results = state.get("extraction_results", {})

    # The extraction results should already be merged from individual nodes
    # This node ensures all results are present and transitions to the next phase

    # Verify all expected results are present
    expected_keys = [
        "score_distribution",
        "flair_distribution",
        "timing_patterns",
        "title_analysis",
        "op_engagement_analysis",
        "upvote_ratio_analysis",
        "post_format_analysis",
        "audience_extraction",
    ]

    missing = [key for key in expected_keys if key not in extraction_results]

    if missing:
        # Fill in missing with empty dicts
        for key in missing:
            extraction_results[key] = {}

    # Calculate summary statistics
    posts = state.get("posts", [])
    comments = state.get("comments", [])

    summary = {
        "total_posts": len(posts),
        "total_comments": len(comments),
        "avg_post_score": round(
            sum(p.get("score", 0) for p in posts) / len(posts), 2
        ) if posts else 0,
        "avg_comment_score": round(
            sum(c.get("score", 0) for c in comments) / len(comments), 2
        ) if comments else 0,
        "unique_authors": len(set(
            p.get("author_name") for p in posts
            if p.get("author_name") and p.get("author_name") != "[deleted]"
        )),
        "extraction_complete": len(missing) == 0,
    }

    extraction_results["summary"] = summary

    return {
        "extraction_results": extraction_results,
        "phase": AnalysisPhase.ANALYZING,
    }
