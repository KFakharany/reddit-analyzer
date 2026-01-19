"""Node for AI-powered persona generation."""

from typing import Any

from src.agents import PersonaAgent
from src.state import WorkflowState


def generate_personas_node(state: WorkflowState) -> dict[str, Any]:
    """Generate audience personas using Claude AI.

    This is an AI node - uses Claude SDK.
    Creates detailed audience personas based on analysis.

    Args:
        state: Current workflow state.

    Returns:
        State update with generated personas.
    """
    extraction_results = state.get("extraction_results", {})
    ai_analysis = state.get("ai_analysis", {})
    community_info = state.get("community_info", {})

    try:
        agent = PersonaAgent()
        response = agent.run({
            "extraction_results": extraction_results,
            "ai_analysis": ai_analysis,
            "community_info": community_info,
        })

        if response.success and response.parsed:
            personas = response.parsed.get("personas", [])
            return {"synthesis": {"personas": personas}}
        else:
            return {
                "synthesis": {
                    "personas": [],
                },
                "errors": [f"Persona generation error: {response.error or 'Failed to parse'}"],
            }

    except Exception as e:
        return {
            "synthesis": {"personas": []},
            "errors": [f"Persona generation error: {str(e)}"],
        }
