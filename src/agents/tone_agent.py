"""Tone analysis agent."""

from typing import Any

from src.agents.base import BaseAgent


class ToneAgent(BaseAgent):
    """Agent for analyzing community tone and communication patterns."""

    def __init__(self):
        """Initialize the tone agent."""
        super().__init__("tone")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create a tone analysis prompt.

        Args:
            data: Should contain 'posts', 'comments', and community info.

        Returns:
            Formatted prompt for tone analysis.
        """
        posts = data.get("posts", [])[:15]
        comments = data.get("comments", [])[:30]
        community_info = data.get("community_info", {})

        # Get high and low scoring content for comparison
        high_score_posts = sorted(posts, key=lambda p: p.get("score", 0), reverse=True)[:5]
        high_score_comments = sorted(comments, key=lambda c: c.get("score", 0), reverse=True)[:10]

        prompt = f"""Analyze the tone and communication style of this Reddit community.

## Community: {community_info.get('display_name', 'Unknown')}
Description: {community_info.get('description', 'No description')[:300]}

## Sample of High-Performing Posts:
{self._format_content(high_score_posts, 'post')}

## Sample of High-Performing Comments:
{self._format_content(high_score_comments, 'comment')}

Provide your analysis as JSON with this structure:
{{
    "overall_tone": {{
        "formality": "<casual|informal|semi-formal|formal|academic>",
        "friendliness": "<hostile|cold|neutral|friendly|welcoming>",
        "expertise_level": "<beginner-friendly|intermediate|expert-level|mixed>"
    }},
    "communication_patterns": {{
        "common_phrases": ["<frequently used phrases>"],
        "jargon_level": "<none|low|medium|high>",
        "jargon_examples": ["<community-specific terms>"],
        "humor_usage": "<rare|occasional|frequent|constant>",
        "meme_culture": "<none|light|moderate|heavy>"
    }},
    "community_dynamics": {{
        "newcomer_treatment": "<hostile|indifferent|helpful|very_welcoming>",
        "gatekeeping_level": "<high|medium|low|none>",
        "debate_style": "<aggressive|passionate|respectful|avoidant>",
        "knowledge_sharing": "<competitive|neutral|collaborative>"
    }},
    "successful_voice_characteristics": [
        "<characteristic of well-received posts/comments>"
    ],
    "voice_to_avoid": [
        "<characteristics that get negative reception>"
    ],
    "recommended_approach": {{
        "tone": "<recommended tone for engagement>",
        "vocabulary": "<vocabulary recommendations>",
        "structure": "<content structure recommendations>"
    }}
}}"""
        return prompt

    def _format_content(self, items: list[dict], content_type: str) -> str:
        """Format content items for the prompt."""
        if not items:
            return f"No {content_type}s available."

        lines = []
        for i, item in enumerate(items, 1):
            score = item.get("score", 0)
            if content_type == "post":
                title = item.get("title", "")
                body = (item.get("selftext", "") or "")[:150]
                lines.append(f"{i}. [{score}] {title}")
                if body:
                    lines.append(f"   {body}...")
            else:
                body = (item.get("body", "") or "")[:200]
                op_tag = " [OP]" if item.get("is_submitter") else ""
                lines.append(f"{i}.{op_tag} [{score}] {body}...")

        return "\n".join(lines)
