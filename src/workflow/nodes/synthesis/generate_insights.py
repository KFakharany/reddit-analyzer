"""Node for AI-powered insight generation."""

from typing import Any

from src.agents import InsightAgent
from src.state import WorkflowState


def generate_insights_node(state: WorkflowState) -> dict[str, Any]:
    """Generate actionable insights using Claude AI.

    This is an AI node - uses Claude SDK.
    Synthesizes all analysis into actionable insights.

    Args:
        state: Current workflow state.

    Returns:
        State update with generated insights.
    """
    extraction_results = state.get("extraction_results", {})
    ai_analysis = state.get("ai_analysis", {})
    synthesis = state.get("synthesis", {})
    community_info = state.get("community_info", {})

    personas = synthesis.get("personas", [])

    try:
        agent = InsightAgent()
        response = agent.run({
            "extraction_results": extraction_results,
            "ai_analysis": ai_analysis,
            "personas": personas,
            "community_info": community_info,
        })

        if response.success and response.parsed:
            return {
                "synthesis": {
                    **synthesis,
                    "insights": response.parsed.get("key_insights", []),
                    "content_strategy": response.parsed.get("content_strategy", {}),
                    "engagement_strategy": response.parsed.get("engagement_strategy", {}),
                    "opportunities": response.parsed.get("opportunity_areas", []),
                    "risks": response.parsed.get("risk_factors", []),
                    "quick_wins": response.parsed.get("quick_wins", []),
                }
            }
        else:
            return {
                "synthesis": {
                    **synthesis,
                    "insights": [],
                },
                "errors": [f"Insight generation error: {response.error or 'Failed to parse'}"],
            }

    except Exception as e:
        return {
            "synthesis": {**synthesis, "insights": []},
            "errors": [f"Insight generation error: {str(e)}"],
        }
