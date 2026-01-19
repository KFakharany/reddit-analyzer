"""Node for extracting score distribution patterns."""

from typing import Any

from src.state import WorkflowState


def extract_scores_node(state: WorkflowState) -> dict[str, Any]:
    """Extract score distribution from posts.

    This is a SCRIPT node - no AI involved.
    Calculates score statistics and distribution buckets.

    Args:
        state: Current workflow state.

    Returns:
        State update with score distribution.
    """
    posts = state.get("posts", [])

    if not posts:
        return {
            "extraction_results": {
                "score_distribution": {
                    "min": 0,
                    "max": 0,
                    "avg": 0,
                    "median": 0,
                    "total_posts": 0,
                    "buckets": {},
                }
            }
        }

    scores = [p.get("score", 0) for p in posts]
    sorted_scores = sorted(scores)

    # Calculate statistics
    n = len(sorted_scores)
    min_score = min(scores)
    max_score = max(scores)
    avg_score = sum(scores) / n
    median_score = (
        sorted_scores[n // 2]
        if n % 2
        else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
    )

    # Score buckets
    buckets = {
        "0-10": 0,
        "11-50": 0,
        "51-100": 0,
        "101-500": 0,
        "501-1000": 0,
        "1000+": 0,
    }

    for score in scores:
        if score <= 10:
            buckets["0-10"] += 1
        elif score <= 50:
            buckets["11-50"] += 1
        elif score <= 100:
            buckets["51-100"] += 1
        elif score <= 500:
            buckets["101-500"] += 1
        elif score <= 1000:
            buckets["501-1000"] += 1
        else:
            buckets["1000+"] += 1

    # Calculate percentiles
    percentiles = {
        "p10": sorted_scores[int(n * 0.1)] if n > 10 else sorted_scores[0],
        "p25": sorted_scores[int(n * 0.25)] if n > 4 else sorted_scores[0],
        "p50": median_score,
        "p75": sorted_scores[int(n * 0.75)] if n > 4 else sorted_scores[-1],
        "p90": sorted_scores[int(n * 0.9)] if n > 10 else sorted_scores[-1],
        "p99": sorted_scores[int(n * 0.99)] if n > 100 else sorted_scores[-1],
    }

    score_distribution = {
        "min": min_score,
        "max": max_score,
        "avg": round(avg_score, 2),
        "median": median_score,
        "total_posts": n,
        "buckets": buckets,
        "percentiles": percentiles,
    }

    return {"extraction_results": {"score_distribution": score_distribution}}
