"""Node for AI-powered promotion analysis."""

from typing import Any

from src.agents import PromotionAgent
from src.state import WorkflowState


def analyze_promotion_node(state: WorkflowState) -> dict[str, Any]:
    """Analyze promotion patterns using Claude AI.

    This is an AI node - uses Claude SDK.
    Analyzes how promotional content is received.

    Args:
        state: Current workflow state.

    Returns:
        State update with promotion analysis.
    """
    posts = state.get("posts", [])
    comments = state.get("top_comments", [])
    extraction_results = state.get("extraction_results", {})

    if not posts:
        return {
            "ai_analysis": {
                "promotion_analysis": {
                    "promotion_reception": {},
                    "error": "No posts available for analysis",
                }
            }
        }

    try:
        agent = PromotionAgent()
        response = agent.run({
            "posts": posts,
            "comments": comments,
            "extraction_results": extraction_results,
        })

        if response.success and response.parsed:
            return {"ai_analysis": {"promotion_analysis": response.parsed}}
        else:
            return {
                "ai_analysis": {
                    "promotion_analysis": {
                        "promotion_reception": {},
                        "error": response.error or "Failed to parse response",
                    }
                }
            }

    except Exception as e:
        return {
            "ai_analysis": {
                "promotion_analysis": {
                    "promotion_reception": {},
                    "error": str(e),
                }
            },
            "errors": [f"Promotion analysis error: {str(e)}"],
        }
