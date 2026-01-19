"""Formatting utilities for Reddit Analyzer."""

from datetime import datetime
from typing import Optional, Union


def format_number(value: Union[int, float], precision: int = 0) -> str:
    """Format a number with thousand separators.

    Args:
        value: Number to format.
        precision: Decimal places for floats.

    Returns:
        Formatted string.
    """
    if isinstance(value, float):
        return f"{value:,.{precision}f}"
    return f"{value:,}"


def format_percentage(value: float, precision: int = 1) -> str:
    """Format a decimal as a percentage.

    Args:
        value: Decimal value (0-1 or 0-100).
        precision: Decimal places.

    Returns:
        Formatted percentage string.
    """
    # Handle both 0-1 and 0-100 ranges
    if value <= 1:
        value = value * 100
    return f"{value:.{precision}f}%"


def format_timestamp(
    dt: Optional[datetime],
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format a datetime object.

    Args:
        dt: Datetime to format.
        format_str: strftime format string.

    Returns:
        Formatted string or "N/A" if None.
    """
    if dt is None:
        return "N/A"
    return dt.strftime(format_str)


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "...",
) -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to add when truncating.

    Returns:
        Truncated text.
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_score_badge(score: int) -> str:
    """Format a score with a contextual badge.

    Args:
        score: Post/comment score.

    Returns:
        Score with emoji badge.
    """
    if score >= 1000:
        return f"🔥 {format_number(score)}"
    elif score >= 100:
        return f"⭐ {format_number(score)}"
    elif score >= 10:
        return f"👍 {format_number(score)}"
    elif score < 0:
        return f"👎 {format_number(score)}"
    return str(score)


def format_time_ago(dt: datetime) -> str:
    """Format a datetime as relative time.

    Args:
        dt: Datetime to format.

    Returns:
        Relative time string (e.g., "2 hours ago").
    """
    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"


def format_karma(karma: int) -> str:
    """Format karma with K/M suffixes.

    Args:
        karma: Karma value.

    Returns:
        Formatted karma string.
    """
    if karma >= 1_000_000:
        return f"{karma / 1_000_000:.1f}M"
    elif karma >= 1_000:
        return f"{karma / 1_000:.1f}K"
    return str(karma)
