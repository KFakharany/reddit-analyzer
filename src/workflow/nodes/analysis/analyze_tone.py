"""Node for AI-powered tone analysis."""

from typing import Any

from src.agents import ToneAgent
from src.state import WorkflowState


def analyze_tone_node(state: WorkflowState) -> dict[str, Any]:
    """Analyze community tone using Claude AI.

    This is an AI node - uses Claude SDK.
    Analyzes communication patterns and community voice.

    Args:
        state: Current workflow state.

    Returns:
        State update with tone analysis.
    """
    posts = state.get("top_posts", [])
    comments = state.get("top_comments", [])
    community_info = state.get("community_info", {})

    if not posts:
        return {
            "ai_analysis": {
                "tone_analysis": {
                    "overall_tone": {},
                    "error": "No posts available for analysis",
                }
            }
        }

    try:
        agent = ToneAgent()
        response = agent.run({
            "posts": posts,
            "comments": comments,
            "community_info": community_info,
        })

        if response.success and response.parsed:
            return {"ai_analysis": {"tone_analysis": response.parsed}}
        else:
            return {
                "ai_analysis": {
                    "tone_analysis": {
                        "overall_tone": {},
                        "error": response.error or "Failed to parse response",
                    }
                }
            }

    except Exception as e:
        return {
            "ai_analysis": {
                "tone_analysis": {
                    "overall_tone": {},
                    "error": str(e),
                }
            },
            "errors": [f"Tone analysis error: {str(e)}"],
        }
