"""Insight generation agent."""

from typing import Any

from src.agents.base import BaseAgent


class InsightAgent(BaseAgent):
    """Agent for synthesizing actionable insights."""

    def __init__(self):
        """Initialize the insight agent."""
        super().__init__("insights")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create an insight synthesis prompt.

        Args:
            data: Should contain all analysis results.

        Returns:
            Formatted prompt for insight generation.
        """
        extraction = data.get("extraction_results", {})
        ai_analysis = data.get("ai_analysis", {})
        personas = data.get("personas", [])
        community_info = data.get("community_info", {})

        prompt = f"""Synthesize all analysis into actionable insights for engaging with this Reddit community.

## Community: {community_info.get('display_name', 'Unknown')}
Subscribers: {community_info.get('subscribers', 'Unknown')}

## Data Summary:

### Content Patterns:
- Score distribution: {extraction.get('score_distribution', {})}
- Best posting times: {extraction.get('timing_patterns', {}).get('best_hour', {})}
- Best posting days: {extraction.get('timing_patterns', {}).get('best_day', {})}
- Title patterns that work: {extraction.get('title_analysis', {}).get('patterns', {})}
- Post formats: {extraction.get('post_format_analysis', {})}

### Audience Profile:
- Skill levels: {extraction.get('audience_extraction', {}).get('skill_levels', {})}
- Tools used: {extraction.get('audience_extraction', {}).get('tools_mentioned', {})}
- Budget profile: {extraction.get('audience_extraction', {}).get('budget_signals', {})}

### AI Analysis Results:
- Sentiment: {ai_analysis.get('sentiment_analysis', {}).get('overall_sentiment', 'unknown')}
- Top pain points: {ai_analysis.get('pain_point_analysis', {}).get('top_pain_points', [])[:3]}
- Tone: {ai_analysis.get('tone_analysis', {}).get('overall_tone', {})}
- Promotion reception: {ai_analysis.get('promotion_analysis', {}).get('promotion_reception', {})}

### Personas:
{self._format_personas(personas)}

Synthesize this into actionable insights. Provide as JSON:
{{
    "key_insights": [
        {{
            "insight": "<insight title>",
            "description": "<detailed explanation>",
            "evidence": ["<supporting data points>"],
            "impact": "<high|medium|low>",
            "actionability": "<immediate|short_term|long_term>"
        }}
    ],
    "content_strategy": {{
        "recommended_topics": ["<topics that will resonate>"],
        "content_formats": ["<formats to use>"],
        "posting_schedule": {{
            "best_days": ["<days>"],
            "best_times": ["<times>"],
            "frequency": "<recommended posting frequency>"
        }},
        "title_formulas": ["<title templates that work>"]
    }},
    "engagement_strategy": {{
        "dos": ["<things to do>"],
        "donts": ["<things to avoid>"],
        "conversation_starters": ["<ways to start engagement>"],
        "value_propositions": ["<what value to offer>"]
    }},
    "opportunity_areas": [
        {{
            "opportunity": "<opportunity description>",
            "target_persona": "<which persona>",
            "approach": "<how to capitalize>",
            "potential_impact": "<high|medium|low>"
        }}
    ],
    "risk_factors": [
        {{
            "risk": "<risk description>",
            "mitigation": "<how to avoid>"
        }}
    ],
    "quick_wins": ["<immediate actions to take>"],
    "long_term_plays": ["<longer-term strategies>"]
}}"""
        return prompt

    def _format_personas(self, personas: list[dict]) -> str:
        """Format personas for the prompt."""
        if not personas:
            return "No personas available."

        lines = []
        for p in personas:
            lines.append(f"- {p.get('name', 'Unknown')}: {p.get('tagline', '')}")
            lines.append(f"  Goals: {', '.join(p.get('goals', [])[:3])}")
            lines.append(f"  Pain points: {', '.join(p.get('pain_points', [])[:3])}")
        return "\n".join(lines)
