"""Node for extracting audience patterns using regex."""

import re
from collections import Counter
from typing import Any

from src.state import WorkflowState


# Regex patterns for audience extraction
PATTERNS = {
    "self_identifications": [
        (r"(?i)i(?:'m| am) a[n]? (\w+(?:\s+\w+)?)", "role"),
        (r"(?i)as a[n]? (\w+(?:\s+\w+)?)", "role"),
        (r"(?i)i work as a[n]? (\w+(?:\s+\w+)?)", "role"),
        (r"(?i)(\w+) here\b", "role"),
    ],
    "skill_levels": [
        (r"(?i)\b(beginner|newbie|noob|just started|new to)\b", "beginner"),
        (r"(?i)\b(intermediate|some experience|learning)\b", "intermediate"),
        (r"(?i)\b(advanced|experienced|senior|expert|professional)\b", "advanced"),
        (r"(?i)\b(years? of experience|been doing this for)\b", "experienced"),
    ],
    "goals": [
        (r"(?i)(?:want|trying|looking) to (\w+(?:\s+\w+){0,3})", "goal"),
        (r"(?i)my goal is to (\w+(?:\s+\w+){0,3})", "goal"),
        (r"(?i)i need to (\w+(?:\s+\w+){0,3})", "need"),
    ],
    "tools": [
        (r"(?i)\b(ChatGPT|GPT-4|GPT-3|Claude|Gemini|Copilot|Midjourney|DALL-E|Stable Diffusion)\b", "ai_tool"),
        (r"(?i)\b(Python|JavaScript|TypeScript|React|Node\.js|Django|Flask)\b", "programming"),
        (r"(?i)\b(VS Code|Cursor|Notion|Obsidian|Slack|Discord)\b", "productivity"),
    ],
    "budget_signals": [
        (r"(?i)\b(free|no budget|can't afford|cheap|affordable)\b", "low_budget"),
        (r"(?i)\b(paid|premium|subscription|willing to pay|budget of)\b", "has_budget"),
        (r"(?i)\$(\d+(?:,\d+)?(?:\.\d+)?)", "specific_amount"),
        (r"(?i)\b(enterprise|business|company|team)\b", "business"),
    ],
    "pain_points": [
        (r"(?i)\b(frustrated|frustrating|annoying|annoyed|hate)\b", "frustration"),
        (r"(?i)\b(struggling|struggle|difficult|hard|challenging)\b", "difficulty"),
        (r"(?i)\b(confused|confusing|don't understand|unclear)\b", "confusion"),
        (r"(?i)\b(slow|sluggish|takes too long|time-consuming)\b", "time"),
        (r"(?i)\b(expensive|costly|pricey|overpriced)\b", "cost"),
    ],
}


def extract_matches(text: str, patterns: list[tuple[str, str]]) -> list[dict[str, str]]:
    """Extract all matches from text using patterns.

    Args:
        text: Text to search.
        patterns: List of (pattern, category) tuples.

    Returns:
        List of match dictionaries with pattern, match, and category.
    """
    matches = []
    for pattern, category in patterns:
        for match in re.finditer(pattern, text):
            matches.append({
                "match": match.group(1) if match.groups() else match.group(0),
                "category": category,
                "full_match": match.group(0),
            })
    return matches


def extract_audience_node(state: WorkflowState) -> dict[str, Any]:
    """Extract audience patterns from posts and comments using regex.

    This is a SCRIPT node - no AI involved.
    Uses regex patterns to identify self-identifications, skills, tools, etc.

    Args:
        state: Current workflow state.

    Returns:
        State update with audience extraction.
    """
    posts = state.get("posts", [])
    comments = state.get("comments", [])

    # Combine all text for analysis
    all_texts = []
    for post in posts:
        all_texts.append(post.get("title", ""))
        all_texts.append(post.get("selftext", "") or "")
    for comment in comments:
        all_texts.append(comment.get("body", "") or "")

    combined_text = " ".join(all_texts)

    # Extract patterns
    self_ids = []
    for text in all_texts:
        self_ids.extend(extract_matches(text, PATTERNS["self_identifications"]))

    skill_levels = extract_matches(combined_text, PATTERNS["skill_levels"])
    goals = extract_matches(combined_text, PATTERNS["goals"])
    tools = extract_matches(combined_text, PATTERNS["tools"])
    budget_signals = extract_matches(combined_text, PATTERNS["budget_signals"])
    pain_points = extract_matches(combined_text, PATTERNS["pain_points"])

    # Count and deduplicate self-identifications
    id_counter = Counter()
    for match in self_ids:
        clean_match = match["match"].lower().strip()
        if len(clean_match) > 2 and clean_match not in ["the", "and", "but", "for"]:
            id_counter[clean_match] += 1

    # Count skill levels
    skill_counter = Counter()
    for match in skill_levels:
        skill_counter[match["category"]] += 1

    # Determine dominant skill level
    if skill_counter:
        dominant_skill = skill_counter.most_common(1)[0][0]
    else:
        dominant_skill = "unknown"

    # Count tools
    tool_counter = Counter()
    for match in tools:
        tool_counter[match["match"]] += 1

    # Count budget signals
    budget_counter = Counter()
    for match in budget_signals:
        budget_counter[match["category"]] += 1

    # Determine budget profile
    low_budget = budget_counter.get("low_budget", 0)
    has_budget = budget_counter.get("has_budget", 0) + budget_counter.get("business", 0)
    if has_budget > low_budget:
        budget_profile = "willing_to_pay"
    elif low_budget > has_budget:
        budget_profile = "price_sensitive"
    else:
        budget_profile = "mixed"

    # Count pain points
    pain_counter = Counter()
    for match in pain_points:
        pain_counter[match["category"]] += 1

    # Calculate skepticism based on pain points and frustration
    total_pain = sum(pain_counter.values())
    frustration_ratio = pain_counter.get("frustration", 0) / max(total_pain, 1)

    if frustration_ratio > 0.3:
        skepticism_level = "very_high"
    elif frustration_ratio > 0.2:
        skepticism_level = "high"
    elif frustration_ratio > 0.1:
        skepticism_level = "medium"
    else:
        skepticism_level = "low"

    audience_extraction = {
        "self_identifications": dict(id_counter.most_common(20)),
        "skill_levels": {
            "distribution": dict(skill_counter),
            "dominant": dominant_skill,
        },
        "goals_sample": [m["match"] for m in goals[:20]],
        "tools_mentioned": dict(tool_counter.most_common(20)),
        "budget_signals": {
            "distribution": dict(budget_counter),
            "profile": budget_profile,
        },
        "pain_points": {
            "distribution": dict(pain_counter),
            "total_mentions": total_pain,
        },
        "skepticism_level": skepticism_level,
        "analysis_stats": {
            "posts_analyzed": len(posts),
            "comments_analyzed": len(comments),
            "total_text_length": len(combined_text),
        },
    }

    return {"extraction_results": {"audience_extraction": audience_extraction}}
