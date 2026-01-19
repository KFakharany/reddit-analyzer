"""Promotion analysis agent."""

from typing import Any

from src.agents.base import BaseAgent


class PromotionAgent(BaseAgent):
    """Agent for analyzing promotional content reception."""

    def __init__(self):
        """Initialize the promotion agent."""
        super().__init__("promotion")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create a promotion analysis prompt.

        Args:
            data: Should contain 'posts', 'comments', and extraction results.

        Returns:
            Formatted prompt for promotion analysis.
        """
        posts = data.get("posts", [])
        comments = data.get("comments", [])[:20]
        extraction = data.get("extraction_results", {})

        # Identify potentially promotional posts
        promo_keywords = ["check out", "i made", "i built", "i created", "my tool",
                         "my app", "my project", "launch", "feedback", "sharing"]

        promo_posts = []
        non_promo_posts = []

        for p in posts:
            title_lower = p.get("title", "").lower()
            selftext_lower = (p.get("selftext", "") or "").lower()

            is_promo = any(kw in title_lower or kw in selftext_lower for kw in promo_keywords)

            if is_promo:
                promo_posts.append(p)
            else:
                non_promo_posts.append(p)

        # Sort by score to see what works
        promo_posts = sorted(promo_posts, key=lambda p: p.get("score", 0), reverse=True)
        non_promo_posts = sorted(non_promo_posts, key=lambda p: p.get("score", 0), reverse=True)

        prompt = f"""Analyze how promotional content is received in this Reddit community.

## Potentially Promotional Posts (sorted by score):
{self._format_posts(promo_posts[:10], "promotional")}

## Non-Promotional Top Posts (for comparison):
{self._format_posts(non_promo_posts[:10], "organic")}

## Flair Distribution Context:
{extraction.get('flair_distribution', {})}

Provide your analysis as JSON with this structure:
{{
    "promotion_reception": {{
        "overall_attitude": "<welcomed|tolerated|skeptical|hostile>",
        "best_performing_promo_type": "<type>",
        "worst_performing_promo_type": "<type>"
    }},
    "successful_patterns": [
        {{
            "pattern": "<what works>",
            "example": "<example from data>",
            "why_it_works": "<explanation>"
        }}
    ],
    "failed_patterns": [
        {{
            "pattern": "<what doesn't work>",
            "warning_signs": ["<indicators of poor reception>"]
        }}
    ],
    "community_rules_signals": {{
        "explicit_rules": ["<rules mentioned in posts/comments>"],
        "implicit_norms": ["<unwritten rules observed>"]
    }},
    "soft_sell_strategies": [
        {{
            "strategy": "<strategy name>",
            "description": "<how to implement>",
            "example": "<example>"
        }}
    ],
    "red_flags": ["<things that will get you downvoted>"],
    "recommendations": {{
        "best_approach": "<overall recommended approach>",
        "content_format": "<recommended format>",
        "timing": "<when to post>",
        "engagement": "<how to engage with comments>"
    }}
}}"""
        return prompt

    def _format_posts(self, posts: list[dict], category: str) -> str:
        """Format posts for the prompt."""
        if not posts:
            return f"No {category} posts identified."

        lines = []
        for i, p in enumerate(posts, 1):
            score = p.get("score", 0)
            ratio = p.get("upvote_ratio", 0)
            flair = p.get("flair_text", "No flair")
            title = p.get("title", "")
            selftext = (p.get("selftext", "") or "")[:150]

            lines.append(f"{i}. [{flair}] {title}")
            lines.append(f"   Score: {score}, Upvote ratio: {ratio:.0%}")
            if selftext:
                lines.append(f"   {selftext}...")
            lines.append("")

        return "\n".join(lines)
