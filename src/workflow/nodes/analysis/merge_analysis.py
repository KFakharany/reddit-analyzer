"""Node for merging AI analysis results."""

from typing import Any

from src.state import WorkflowState, AnalysisPhase


def merge_analysis_node(state: WorkflowState) -> dict[str, Any]:
    """Merge all AI analysis results.

    This is a SCRIPT node - no AI involved.
    Combines all AI analysis results and transitions to synthesis phase.

    Args:
        state: Current workflow state.

    Returns:
        State update with merged analysis.
    """
    ai_analysis = state.get("ai_analysis", {})

    # Verify all expected results are present
    expected_keys = [
        "sentiment_analysis",
        "pain_point_analysis",
        "tone_analysis",
        "promotion_analysis",
    ]

    missing = [key for key in expected_keys if key not in ai_analysis]
    errors = []

    for key in missing:
        ai_analysis[key] = {"error": "Analysis not performed"}

    # Check for errors in analyses
    for key in expected_keys:
        if ai_analysis.get(key, {}).get("error"):
            errors.append(f"{key}: {ai_analysis[key]['error']}")

    # Create analysis summary
    analysis_summary = {
        "sentiment": ai_analysis.get("sentiment_analysis", {}).get("overall_sentiment", "unknown"),
        "pain_points_found": len(
            ai_analysis.get("pain_point_analysis", {}).get("top_pain_points", [])
        ),
        "tone_formality": ai_analysis.get("tone_analysis", {}).get("overall_tone", {}).get("formality", "unknown"),
        "promotion_attitude": ai_analysis.get("promotion_analysis", {}).get("promotion_reception", {}).get("overall_attitude", "unknown"),
        "analysis_complete": len(missing) == 0 and len(errors) == 0,
        "errors": errors,
    }

    ai_analysis["summary"] = analysis_summary

    return {
        "ai_analysis": ai_analysis,
        "phase": AnalysisPhase.SYNTHESIZING,
    }
