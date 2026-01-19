"""Node for extracting timing patterns."""

from collections import Counter
from datetime import datetime
from typing import Any

from src.state import WorkflowState


def extract_timing_node(state: WorkflowState) -> dict[str, Any]:
    """Extract timing patterns from posts.

    This is a SCRIPT node - no AI involved.
    Analyzes post timing by hour and day of week.

    Args:
        state: Current workflow state.

    Returns:
        State update with timing patterns.
    """
    posts = state.get("posts", [])

    if not posts:
        return {
            "extraction_results": {
                "timing_patterns": {
                    "by_hour": {},
                    "by_day": {},
                    "best_hour": None,
                    "best_day": None,
                }
            }
        }

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    hours = []
    days = []
    hour_scores = {}
    day_scores = {}

    for post in posts:
        created = post.get("created_utc")
        score = post.get("score", 0)

        if created:
            if isinstance(created, datetime):
                dt = created
            else:
                dt = datetime.utcfromtimestamp(created)

            hour = dt.hour
            day = dt.weekday()

            hours.append(hour)
            days.append(day)

            # Track scores by hour
            if hour not in hour_scores:
                hour_scores[hour] = []
            hour_scores[hour].append(score)

            # Track scores by day
            if day not in day_scores:
                day_scores[day] = []
            day_scores[day].append(score)

    # Count by hour
    hour_counts = Counter(hours)
    by_hour = {}
    for hour in range(24):
        count = hour_counts.get(hour, 0)
        scores = hour_scores.get(hour, [])
        by_hour[f"{hour:02d}:00"] = {
            "count": count,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "percentage": round(count / len(posts) * 100, 1) if posts else 0,
        }

    # Count by day
    day_counts = Counter(days)
    by_day = {}
    for day in range(7):
        count = day_counts.get(day, 0)
        scores = day_scores.get(day, [])
        by_day[day_names[day]] = {
            "count": count,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "percentage": round(count / len(posts) * 100, 1) if posts else 0,
        }

    # Find best posting times
    best_hour = None
    best_hour_score = 0
    for hour, data in by_hour.items():
        if data["count"] >= 3 and data["avg_score"] > best_hour_score:
            best_hour = hour
            best_hour_score = data["avg_score"]

    best_day = None
    best_day_score = 0
    for day, data in by_day.items():
        if data["count"] >= 3 and data["avg_score"] > best_day_score:
            best_day = day
            best_day_score = data["avg_score"]

    timing_patterns = {
        "by_hour": by_hour,
        "by_day": by_day,
        "best_hour": {
            "hour": best_hour,
            "avg_score": best_hour_score,
        }
        if best_hour
        else None,
        "best_day": {
            "day": best_day,
            "avg_score": best_day_score,
        }
        if best_day
        else None,
        "total_posts_analyzed": len(posts),
    }

    return {"extraction_results": {"timing_patterns": timing_patterns}}
