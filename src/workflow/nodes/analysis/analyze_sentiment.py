"""Node for AI-powered sentiment analysis."""

from typing import Any

from src.agents import SentimentAgent
from src.state import WorkflowState


def analyze_sentiment_node(state: WorkflowState) -> dict[str, Any]:
    """Analyze sentiment patterns using Claude AI.

    This is an AI node - uses Claude SDK.
    Analyzes sentiment distribution and emotional patterns.

    Args:
        state: Current workflow state.

    Returns:
        State update with sentiment analysis.
    """
    posts = state.get("top_posts", [])
    comments = state.get("top_comments", [])

    if not posts:
        return {
            "ai_analysis": {
                "sentiment_analysis": {
                    "overall_sentiment": "unknown",
                    "error": "No posts available for analysis",
                }
            }
        }

    try:
        agent = SentimentAgent()
        response = agent.run({
            "posts": posts,
            "comments": comments,
        })

        if response.success and response.parsed:
            return {"ai_analysis": {"sentiment_analysis": response.parsed}}
        else:
            return {
                "ai_analysis": {
                    "sentiment_analysis": {
                        "overall_sentiment": "unknown",
                        "error": response.error or "Failed to parse response",
                        "raw_response": response.content[:500] if response.content else None,
                    }
                }
            }

    except Exception as e:
        return {
            "ai_analysis": {
                "sentiment_analysis": {
                    "overall_sentiment": "unknown",
                    "error": str(e),
                }
            },
            "errors": [f"Sentiment analysis error: {str(e)}"],
        }
