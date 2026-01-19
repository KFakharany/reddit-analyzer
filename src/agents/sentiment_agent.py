"""Sentiment analysis agent."""

from typing import Any

from src.agents.base import BaseAgent


class SentimentAgent(BaseAgent):
    """Agent for analyzing sentiment in Reddit content."""

    def __init__(self):
        """Initialize the sentiment agent."""
        super().__init__("sentiment")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create a sentiment analysis prompt.

        Args:
            data: Should contain 'posts' and 'comments' lists.

        Returns:
            Formatted prompt for sentiment analysis.
        """
        posts = data.get("posts", [])[:20]  # Limit for token efficiency
        comments = data.get("comments", [])[:30]

        # Format posts
        post_samples = []
        for p in posts:
            post_samples.append({
                "title": p.get("title", ""),
                "score": p.get("score", 0),
                "flair": p.get("flair_text", ""),
                "snippet": (p.get("selftext", "") or "")[:200],
            })

        # Format comments
        comment_samples = []
        for c in comments:
            comment_samples.append({
                "body": (c.get("body", "") or "")[:200],
                "score": c.get("score", 0),
                "is_op": c.get("is_submitter", False),
            })

        prompt = f"""Analyze the sentiment patterns in this Reddit community data.

## Top Posts (by score):
{self._format_posts(post_samples)}

## Top Comments (by score):
{self._format_comments(comment_samples)}

Provide your analysis as JSON with this structure:
{{
    "overall_sentiment": "positive|negative|neutral|mixed",
    "sentiment_distribution": {{
        "positive": <percentage>,
        "negative": <percentage>,
        "neutral": <percentage>
    }},
    "emotional_undertones": [
        {{"emotion": "<emotion>", "frequency": "<high|medium|low>", "examples": ["<example>"]}}
    ],
    "topic_sentiments": [
        {{"topic": "<topic>", "sentiment": "<sentiment>", "notes": "<notes>"}}
    ],
    "key_observations": ["<observation>"],
    "sentiment_drivers": {{
        "positive_drivers": ["<what makes posts positive>"],
        "negative_drivers": ["<what causes negative sentiment>"]
    }}
}}"""
        return prompt

    def _format_posts(self, posts: list[dict]) -> str:
        """Format posts for the prompt."""
        lines = []
        for i, p in enumerate(posts, 1):
            lines.append(f"{i}. [{p['flair'] or 'No flair'}] {p['title']} (score: {p['score']})")
            if p['snippet']:
                lines.append(f"   {p['snippet'][:150]}...")
        return "\n".join(lines)

    def _format_comments(self, comments: list[dict]) -> str:
        """Format comments for the prompt."""
        lines = []
        for i, c in enumerate(comments, 1):
            op_tag = " [OP]" if c['is_op'] else ""
            lines.append(f"{i}.{op_tag} (score: {c['score']}) {c['body'][:150]}...")
        return "\n".join(lines)
