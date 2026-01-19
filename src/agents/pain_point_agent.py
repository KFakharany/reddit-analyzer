"""Pain point analysis agent."""

from typing import Any

from src.agents.base import BaseAgent


class PainPointAgent(BaseAgent):
    """Agent for identifying user pain points in Reddit content."""

    def __init__(self):
        """Initialize the pain point agent."""
        super().__init__("pain_points")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create a pain point analysis prompt.

        Args:
            data: Should contain 'posts', 'comments', and optionally 'extraction_results'.

        Returns:
            Formatted prompt for pain point analysis.
        """
        posts = data.get("posts", [])[:20]
        comments = data.get("comments", [])[:40]
        extraction = data.get("extraction_results", {})

        # Extract question posts and help-seeking content
        question_posts = [
            p for p in posts
            if "?" in p.get("title", "") or
            any(word in p.get("title", "").lower() for word in ["help", "how", "why", "can't", "issue", "problem"])
        ]

        # Extract complaint/frustration comments
        frustration_comments = [
            c for c in comments
            if any(word in (c.get("body", "") or "").lower()
                   for word in ["frustrat", "annoy", "hate", "terrible", "awful", "struggle", "difficult", "confus"])
        ]

        prompt = f"""Analyze the pain points and challenges expressed in this Reddit community.

## Questions & Help Requests:
{self._format_questions(question_posts[:15])}

## Frustration Expressions:
{self._format_frustrations(frustration_comments[:15])}

## Audience Context (from pattern extraction):
- Common self-identifications: {extraction.get('audience_extraction', {}).get('self_identifications', {})}
- Skill level distribution: {extraction.get('audience_extraction', {}).get('skill_levels', {})}
- Previously detected pain signals: {extraction.get('audience_extraction', {}).get('pain_points', {})}

Provide your analysis as JSON with this structure:
{{
    "pain_point_categories": [
        {{
            "category": "<category name>",
            "frequency": "<high|medium|low>",
            "intensity": "<high|medium|low>",
            "examples": ["<specific example from data>"],
            "underlying_need": "<what users actually need>"
        }}
    ],
    "top_pain_points": [
        {{
            "pain_point": "<specific pain point>",
            "who_experiences_it": "<user segment>",
            "context": "<when/why this occurs>",
            "potential_solutions": ["<possible solutions>"]
        }}
    ],
    "unmet_needs": ["<needs not being addressed>"],
    "frustration_patterns": {{
        "common_triggers": ["<what triggers frustration>"],
        "emotional_responses": ["<how users express frustration>"]
    }},
    "opportunity_areas": ["<areas where solutions could help>"]
}}"""
        return prompt

    def _format_questions(self, posts: list[dict]) -> str:
        """Format question posts for the prompt."""
        if not posts:
            return "No specific questions found."
        lines = []
        for i, p in enumerate(posts, 1):
            lines.append(f"{i}. {p.get('title', '')} (score: {p.get('score', 0)})")
            selftext = p.get("selftext", "") or ""
            if selftext:
                lines.append(f"   {selftext[:200]}...")
        return "\n".join(lines)

    def _format_frustrations(self, comments: list[dict]) -> str:
        """Format frustration comments for the prompt."""
        if not comments:
            return "No specific frustration expressions found."
        lines = []
        for i, c in enumerate(comments, 1):
            body = (c.get("body", "") or "")[:200]
            lines.append(f"{i}. {body}...")
        return "\n".join(lines)
