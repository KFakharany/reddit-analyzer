"""Node for AI-powered pain point analysis."""

from typing import Any

from src.agents import PainPointAgent
from src.state import WorkflowState


def analyze_pain_points_node(state: WorkflowState) -> dict[str, Any]:
    """Analyze pain points using Claude AI.

    This is an AI node - uses Claude SDK.
    Identifies and categorizes user pain points and challenges.

    Args:
        state: Current workflow state.

    Returns:
        State update with pain point analysis.
    """
    posts = state.get("top_posts", [])
    comments = state.get("top_comments", [])
    extraction_results = state.get("extraction_results", {})

    if not posts:
        return {
            "ai_analysis": {
                "pain_point_analysis": {
                    "pain_point_categories": [],
                    "error": "No posts available for analysis",
                }
            }
        }

    try:
        agent = PainPointAgent()
        response = agent.run({
            "posts": posts,
            "comments": comments,
            "extraction_results": extraction_results,
        })

        if response.success and response.parsed:
            return {"ai_analysis": {"pain_point_analysis": response.parsed}}
        else:
            return {
                "ai_analysis": {
                    "pain_point_analysis": {
                        "pain_point_categories": [],
                        "error": response.error or "Failed to parse response",
                    }
                }
            }

    except Exception as e:
        return {
            "ai_analysis": {
                "pain_point_analysis": {
                    "pain_point_categories": [],
                    "error": str(e),
                }
            },
            "errors": [f"Pain point analysis error: {str(e)}"],
        }
