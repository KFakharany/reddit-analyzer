"""Report generation agent."""

from typing import Any

from src.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    """Agent for generating comprehensive analysis reports."""

    def __init__(self):
        """Initialize the report agent."""
        super().__init__("report")

    def _create_prompt(self, data: dict[str, Any]) -> str:
        """Create a report generation prompt.

        Args:
            data: Should contain all analysis and synthesis results.

        Returns:
            Formatted prompt for report generation.
        """
        community_info = data.get("community_info", {})
        extraction = data.get("extraction_results", {})
        ai_analysis = data.get("ai_analysis", {})
        personas = data.get("personas", [])
        insights = data.get("insights", [])

        prompt = f"""Generate a comprehensive community analysis report in Markdown format.

## Community Information:
- Name: {community_info.get('display_name', 'Unknown')}
- Subscribers: {community_info.get('subscribers', 'Unknown')}
- Description: {community_info.get('description', 'No description')}

## Data Collection Summary:
- Posts analyzed: {extraction.get('summary', {}).get('total_posts', 0)}
- Comments analyzed: {extraction.get('summary', {}).get('total_comments', 0)}
- Unique authors: {extraction.get('summary', {}).get('unique_authors', 0)}

## Score Distribution:
{extraction.get('score_distribution', {})}

## Timing Patterns:
{extraction.get('timing_patterns', {})}

## Flair Distribution:
{extraction.get('flair_distribution', {})}

## Title Analysis:
{extraction.get('title_analysis', {})}

## Engagement Metrics:
- OP Engagement: {extraction.get('op_engagement_analysis', {})}
- Upvote Ratios: {extraction.get('upvote_ratio_analysis', {})}
- Post Formats: {extraction.get('post_format_analysis', {})}

## Audience Patterns:
{extraction.get('audience_extraction', {})}

## AI Analysis:

### Sentiment:
{ai_analysis.get('sentiment_analysis', {})}

### Pain Points:
{ai_analysis.get('pain_point_analysis', {})}

### Tone:
{ai_analysis.get('tone_analysis', {})}

### Promotion Analysis:
{ai_analysis.get('promotion_analysis', {})}

## Personas:
{personas}

## Key Insights:
{insights}

---

Generate a professional, well-formatted Markdown report with the following sections:

1. **Executive Summary** - 3-5 bullet points of key findings
2. **Community Overview** - Brief description and key stats
3. **Audience Profile** - Who uses this community
4. **Content Analysis** - What content performs well
5. **Engagement Patterns** - How to engage effectively
6. **Opportunities & Recommendations** - Actionable next steps
7. **Risks & Considerations** - What to watch out for

Use tables, bullet points, and clear headers. Make it actionable and easy to scan.
Do NOT wrap the output in code blocks - just output the raw Markdown."""
        return prompt

    def _parse_response(self, content: str) -> dict[str, Any] | None:
        """Override to return markdown content directly."""
        # For reports, we want the raw markdown, not parsed JSON
        return {"markdown": content.strip()}
