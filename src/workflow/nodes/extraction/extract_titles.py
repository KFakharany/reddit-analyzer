"""Node for extracting title patterns."""

import re
from typing import Any

from src.state import WorkflowState


def extract_titles_node(state: WorkflowState) -> dict[str, Any]:
    """Extract title patterns from posts.

    This is a SCRIPT node - no AI involved.
    Analyzes title length, punctuation, and patterns.

    Args:
        state: Current workflow state.

    Returns:
        State update with title analysis.
    """
    posts = state.get("posts", [])

    if not posts:
        return {
            "extraction_results": {
                "title_analysis": {
                    "avg_length": 0,
                    "patterns": {},
                    "word_frequency": {},
                }
            }
        }

    titles = [p.get("title", "") for p in posts]
    scores = [p.get("score", 0) for p in posts]

    # Length analysis
    lengths = [len(t) for t in titles]
    word_counts = [len(t.split()) for t in titles]

    # Pattern detection
    patterns = {
        "question": {"count": 0, "scores": [], "pattern": r"\?"},
        "exclamation": {"count": 0, "scores": [], "pattern": r"!"},
        "all_caps_word": {"count": 0, "scores": [], "pattern": r"\b[A-Z]{2,}\b"},
        "number": {"count": 0, "scores": [], "pattern": r"\d+"},
        "brackets": {"count": 0, "scores": [], "pattern": r"[\[\]\(\)]"},
        "how_to": {"count": 0, "scores": [], "pattern": r"(?i)how\s+to"},
        "asking_help": {"count": 0, "scores": [], "pattern": r"(?i)(help|please|need|looking for)"},
        "sharing": {"count": 0, "scores": [], "pattern": r"(?i)(i made|i built|i created|just finished|check out)"},
        "meta": {"count": 0, "scores": [], "pattern": r"(?i)(meta|announcement|mod|rule)"},
    }

    for i, title in enumerate(titles):
        score = scores[i]
        for pattern_name, pattern_data in patterns.items():
            if re.search(pattern_data["pattern"], title):
                pattern_data["count"] += 1
                pattern_data["scores"].append(score)

    # Calculate pattern stats
    pattern_stats = {}
    for pattern_name, pattern_data in patterns.items():
        count = pattern_data["count"]
        pattern_scores = pattern_data["scores"]
        pattern_stats[pattern_name] = {
            "count": count,
            "percentage": round(count / len(posts) * 100, 1),
            "avg_score": round(sum(pattern_scores) / len(pattern_scores), 2)
            if pattern_scores
            else 0,
        }

    # Length buckets
    length_buckets = {
        "short (0-50)": {"count": 0, "scores": []},
        "medium (51-100)": {"count": 0, "scores": []},
        "long (101-150)": {"count": 0, "scores": []},
        "very_long (150+)": {"count": 0, "scores": []},
    }

    for i, length in enumerate(lengths):
        score = scores[i]
        if length <= 50:
            length_buckets["short (0-50)"]["count"] += 1
            length_buckets["short (0-50)"]["scores"].append(score)
        elif length <= 100:
            length_buckets["medium (51-100)"]["count"] += 1
            length_buckets["medium (51-100)"]["scores"].append(score)
        elif length <= 150:
            length_buckets["long (101-150)"]["count"] += 1
            length_buckets["long (101-150)"]["scores"].append(score)
        else:
            length_buckets["very_long (150+)"]["count"] += 1
            length_buckets["very_long (150+)"]["scores"].append(score)

    length_stats = {}
    for bucket_name, bucket_data in length_buckets.items():
        count = bucket_data["count"]
        bucket_scores = bucket_data["scores"]
        length_stats[bucket_name] = {
            "count": count,
            "percentage": round(count / len(posts) * 100, 1),
            "avg_score": round(sum(bucket_scores) / len(bucket_scores), 2)
            if bucket_scores
            else 0,
        }

    # Common starting words
    starting_words = []
    for title in titles:
        words = title.split()
        if words:
            starting_words.append(words[0].lower())

    start_word_counts = {}
    for word in starting_words:
        start_word_counts[word] = start_word_counts.get(word, 0) + 1

    # Top 10 starting words
    top_starting = dict(
        sorted(start_word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    )

    title_analysis = {
        "avg_length": round(sum(lengths) / len(lengths), 1),
        "avg_word_count": round(sum(word_counts) / len(word_counts), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "patterns": pattern_stats,
        "length_distribution": length_stats,
        "top_starting_words": top_starting,
        "total_posts": len(posts),
    }

    return {"extraction_results": {"title_analysis": title_analysis}}
