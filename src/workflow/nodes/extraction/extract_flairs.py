"""Node for extracting flair distribution patterns."""

from collections import Counter
from typing import Any

from src.state import WorkflowState


def extract_flairs_node(state: WorkflowState) -> dict[str, Any]:
    """Extract flair distribution from posts.

    This is a SCRIPT node - no AI involved.
    Counts flair usage and calculates statistics.

    Args:
        state: Current workflow state.

    Returns:
        State update with flair distribution.
    """
    posts = state.get("posts", [])

    if not posts:
        return {
            "extraction_results": {
                "flair_distribution": {
                    "flairs": {},
                    "no_flair_count": 0,
                    "total_posts": 0,
                    "unique_flairs": 0,
                }
            }
        }

    # Count flairs
    flairs = [p.get("flair_text") for p in posts]
    flair_counts = Counter(flairs)

    # Separate no-flair posts
    no_flair_count = flair_counts.pop(None, 0)

    # Sort by count
    sorted_flairs = dict(flair_counts.most_common())

    # Calculate flair statistics
    flair_stats = {}
    for flair, count in sorted_flairs.items():
        flair_posts = [p for p in posts if p.get("flair_text") == flair]
        scores = [p.get("score", 0) for p in flair_posts]

        flair_stats[flair] = {
            "count": count,
            "percentage": round(count / len(posts) * 100, 1),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }

    flair_distribution = {
        "flairs": flair_stats,
        "no_flair_count": no_flair_count,
        "no_flair_percentage": round(no_flair_count / len(posts) * 100, 1),
        "total_posts": len(posts),
        "unique_flairs": len(sorted_flairs),
    }

    return {"extraction_results": {"flair_distribution": flair_distribution}}
