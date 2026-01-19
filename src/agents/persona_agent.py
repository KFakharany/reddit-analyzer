"""Persona generation agent."""

from typing import Any

from src.agents.base import BaseAgent


class PersonaAgent(BaseAgent):
    """Agent for generating audience personas."""

    def __init__(self):
        """Initialize the persona agent."""
        super().__init__("persona")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create a persona generation prompt.

        Args:
            data: Should contain extraction results and AI analysis results.

        Returns:
            Formatted prompt for persona generation.
        """
        extraction = data.get("extraction_results", {})
        ai_analysis = data.get("ai_analysis", {})
        community_info = data.get("community_info", {})

        audience = extraction.get("audience_extraction", {})
        sentiment = ai_analysis.get("sentiment_analysis", {})
        pain_points = ai_analysis.get("pain_point_analysis", {})
        tone = ai_analysis.get("tone_analysis", {})

        prompt = f"""Create detailed audience personas for this Reddit community.

## Community: {community_info.get('display_name', 'Unknown')}
{community_info.get('description', '')[:300]}

## Audience Data:

### Self-Identifications Found:
{audience.get('self_identifications', {})}

### Skill Level Distribution:
{audience.get('skill_levels', {})}

### Tools Mentioned:
{audience.get('tools_mentioned', {})}

### Budget Signals:
{audience.get('budget_signals', {})}

### Pain Points Identified:
{pain_points.get('top_pain_points', [])}

### Sentiment Profile:
{sentiment.get('overall_sentiment', 'unknown')}
Emotional undertones: {sentiment.get('emotional_undertones', [])}

### Community Tone:
{tone.get('overall_tone', {})}
{tone.get('community_dynamics', {})}

Based on this data, create 3-5 distinct personas that represent the main audience segments.

Provide your personas as JSON with this structure:
{{
    "personas": [
        {{
            "name": "<persona name - make it memorable>",
            "tagline": "<one line description>",
            "background": {{
                "profession": "<job/role>",
                "experience_level": "<beginner|intermediate|advanced|expert>",
                "company_type": "<startup|enterprise|freelance|student|hobbyist>"
            }},
            "demographics": {{
                "age_range": "<estimated age range>",
                "likely_location": "<geographic hints>"
            }},
            "goals": ["<primary goals>"],
            "pain_points": ["<specific challenges they face>"],
            "motivations": ["<what drives them>"],
            "behaviors": {{
                "posting_patterns": "<how they engage>",
                "content_preferences": "<what they consume>",
                "typical_questions": ["<questions they ask>"]
            }},
            "tools_used": ["<tools they mention/use>"],
            "content_that_resonates": ["<content types they engage with>"],
            "how_to_reach_them": "<approach for engagement>",
            "percentage_of_community": "<estimated % of community>"
        }}
    ],
    "persona_summary": {{
        "primary_persona": "<most common persona name>",
        "key_insight": "<main insight about the audience>",
        "diversity_note": "<note about audience diversity>"
    }}
}}"""
        return prompt
