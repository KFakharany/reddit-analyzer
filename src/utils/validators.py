"""Validation utilities for Reddit Analyzer."""

import re
from typing import Any


def validate_subreddit_name(name: str) -> tuple[bool, str]:
    """Validate a subreddit name.

    Args:
        name: Subreddit name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not name:
        return False, "Subreddit name cannot be empty"

    # Remove r/ prefix if present
    if name.lower().startswith("r/"):
        name = name[2:]

    # Check length
    if len(name) < 2:
        return False, "Subreddit name must be at least 2 characters"

    if len(name) > 21:
        return False, "Subreddit name cannot exceed 21 characters"

    # Check characters (alphanumeric and underscores only)
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return False, "Subreddit name can only contain letters, numbers, and underscores"

    # Check for reserved names
    reserved = ["admin", "reddit", "moderator", "mod", "null", "undefined"]
    if name.lower() in reserved:
        return False, f"'{name}' is a reserved name"

    return True, ""


def validate_collection_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate collection configuration.

    Args:
        config: Collection configuration dictionary.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []

    # Validate posts_limit
    posts_limit = config.get("posts_limit", 100)
    if not isinstance(posts_limit, int):
        errors.append("posts_limit must be an integer")
    elif posts_limit < 1:
        errors.append("posts_limit must be at least 1")
    elif posts_limit > 1000:
        errors.append("posts_limit cannot exceed 1000")

    # Validate comments_limit
    comments_limit = config.get("comments_limit", 50)
    if not isinstance(comments_limit, int):
        errors.append("comments_limit must be an integer")
    elif comments_limit < 0:
        errors.append("comments_limit cannot be negative")
    elif comments_limit > 500:
        errors.append("comments_limit cannot exceed 500")

    # Validate sort_methods
    sort_methods = config.get("sort_methods", ["hot", "top", "new"])
    valid_sorts = {"hot", "new", "top", "rising", "controversial"}
    if not isinstance(sort_methods, list):
        errors.append("sort_methods must be a list")
    elif not sort_methods:
        errors.append("sort_methods cannot be empty")
    else:
        invalid = set(sort_methods) - valid_sorts
        if invalid:
            errors.append(f"Invalid sort methods: {invalid}")

    # Validate time_filter
    time_filter = config.get("time_filter", "week")
    valid_filters = {"hour", "day", "week", "month", "year", "all"}
    if time_filter not in valid_filters:
        errors.append(f"Invalid time_filter: {time_filter}. Must be one of {valid_filters}")

    return len(errors) == 0, errors


def validate_run_id(run_id: Any) -> tuple[bool, str]:
    """Validate a collection run ID.

    Args:
        run_id: Run ID to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if run_id is None:
        return False, "Run ID cannot be None"

    if not isinstance(run_id, int):
        return False, "Run ID must be an integer"

    if run_id < 1:
        return False, "Run ID must be positive"

    return True, ""


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize text content for safe processing.

    Args:
        text: Text to sanitize.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
    if not text:
        return ""

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize whitespace
    text = " ".join(text.split())

    return text
