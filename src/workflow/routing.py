"""Routing logic for LangGraph workflow."""

from typing import Literal

from src.state import WorkflowState, AnalysisPhase, WorkflowStatus


def should_collect_data(state: WorkflowState) -> Literal["collect", "load_existing"]:
    """Determine whether to collect new data or load existing.

    Args:
        state: Current workflow state.

    Returns:
        "collect" to fetch new data, "load_existing" to use existing run.
    """
    if state.get("skip_collection"):
        return "load_existing"

    if state.get("existing_run_id"):
        return "load_existing"

    return "collect"


def should_run_ai(state: WorkflowState) -> Literal["analyze", "skip_to_output"]:
    """Determine whether to run AI analysis.

    Args:
        state: Current workflow state.

    Returns:
        "analyze" to run AI analysis, "skip_to_output" to skip.
    """
    if state.get("skip_ai"):
        return "skip_to_output"

    # Check if we have data to analyze
    posts = state.get("posts", [])
    if not posts:
        return "skip_to_output"

    return "analyze"


def check_for_errors(state: WorkflowState) -> Literal["continue", "abort"]:
    """Check if there are critical errors that should abort the workflow.

    Args:
        state: Current workflow state.

    Returns:
        "abort" if critical error, "continue" otherwise.
    """
    error = state.get("error")
    if error:
        return "abort"

    # Check if collection failed completely
    posts = state.get("posts", [])
    if state.get("phase") == AnalysisPhase.COLLECTING and not posts:
        return "abort"

    return "continue"


def get_next_extraction_node(state: WorkflowState) -> str:
    """Get the next extraction node to run.

    For parallel execution tracking. In LangGraph, this is handled
    by the graph structure, but this helper can be useful for
    debugging and logging.

    Args:
        state: Current workflow state.

    Returns:
        Name of next extraction node or "merge" if done.
    """
    results = state.get("extraction_results", {})

    required = [
        "score_distribution",
        "flair_distribution",
        "timing_patterns",
        "title_analysis",
        "op_engagement_analysis",
        "audience_extraction",
    ]

    for key in required:
        if key not in results:
            return f"extract_{key.replace('_distribution', '').replace('_analysis', '').replace('_extraction', '')}"

    return "merge"


def get_next_analysis_node(state: WorkflowState) -> str:
    """Get the next analysis node to run.

    Args:
        state: Current workflow state.

    Returns:
        Name of next analysis node or "merge" if done.
    """
    ai_analysis = state.get("ai_analysis", {})

    required = [
        "sentiment_analysis",
        "pain_point_analysis",
        "tone_analysis",
        "promotion_analysis",
    ]

    for key in required:
        if key not in ai_analysis:
            return f"analyze_{key.replace('_analysis', '')}"

    return "merge"


def is_workflow_complete(state: WorkflowState) -> bool:
    """Check if the workflow is complete.

    Args:
        state: Current workflow state.

    Returns:
        True if workflow is complete.
    """
    return state.get("phase") == AnalysisPhase.DONE


def get_workflow_status(state: WorkflowState) -> WorkflowStatus:
    """Get the current workflow status.

    Args:
        state: Current workflow state.

    Returns:
        Current WorkflowStatus.
    """
    if state.get("error"):
        return WorkflowStatus.FAILED

    if state.get("phase") == AnalysisPhase.DONE:
        return WorkflowStatus.COMPLETED

    return WorkflowStatus.RUNNING
