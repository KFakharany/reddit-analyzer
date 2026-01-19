"""Node for AI-powered report generation."""

import os
from datetime import datetime
from typing import Any

from src.agents import ReportAgent
from src.state import WorkflowState, AnalysisPhase


def generate_report_node(state: WorkflowState) -> dict[str, Any]:
    """Generate comprehensive report using Claude AI.

    This is an AI node - uses Claude SDK.
    Generates a markdown report from all analysis.

    Args:
        state: Current workflow state.

    Returns:
        State update with report content and path.
    """
    extraction_results = state.get("extraction_results", {})
    ai_analysis = state.get("ai_analysis", {})
    synthesis = state.get("synthesis", {})
    community_info = state.get("community_info", {})
    output_dir = state.get("output_dir", "./output")

    personas = synthesis.get("personas", [])
    insights = synthesis.get("insights", [])

    try:
        agent = ReportAgent()
        response = agent.run({
            "extraction_results": extraction_results,
            "ai_analysis": ai_analysis,
            "personas": personas,
            "insights": insights,
            "community_info": community_info,
        })

        if response.success and response.parsed:
            report_content = response.parsed.get("markdown", response.content)

            # Save report to file
            community_name = community_info.get("name", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{community_name}_COMMUNITY_SUMMARY_{timestamp}.md"

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            report_path = os.path.join(output_dir, filename)

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            return {
                "synthesis": {
                    **synthesis,
                    "report_content": report_content,
                },
                "report_path": report_path,
                "phase": AnalysisPhase.DONE,
            }
        else:
            return {
                "synthesis": {
                    **synthesis,
                    "report_content": "",
                },
                "errors": [f"Report generation error: {response.error or 'Failed to generate'}"],
                "phase": AnalysisPhase.DONE,
            }

    except Exception as e:
        return {
            "synthesis": {**synthesis, "report_content": ""},
            "errors": [f"Report generation error: {str(e)}"],
            "phase": AnalysisPhase.DONE,
        }
