"""Tests for validation utilities."""

import pytest

from src.utils.validators import (
    validate_subreddit_name,
    validate_collection_config,
    validate_run_id,
    sanitize_text,
)


class TestValidateSubredditName:
    """Tests for subreddit name validation."""

    def test_valid_name(self):
        """Test valid subreddit names."""
        valid_names = [
            "Python",
            "PromptEngineering",
            "micro_saas",
            "AskReddit",
            "programming",
        ]
        for name in valid_names:
            is_valid, error = validate_subreddit_name(name)
            assert is_valid, f"'{name}' should be valid: {error}"

    def test_with_r_prefix(self):
        """Test names with r/ prefix."""
        is_valid, _ = validate_subreddit_name("r/Python")
        assert is_valid

    def test_empty_name(self):
        """Test empty name."""
        is_valid, error = validate_subreddit_name("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_too_short(self):
        """Test names that are too short."""
        is_valid, error = validate_subreddit_name("a")
        assert not is_valid
        assert "2 characters" in error

    def test_too_long(self):
        """Test names that are too long."""
        is_valid, error = validate_subreddit_name("a" * 25)
        assert not is_valid
        assert "21 characters" in error

    def test_invalid_characters(self):
        """Test names with invalid characters."""
        invalid_names = ["test-sub", "test.sub", "test sub", "test@sub"]
        for name in invalid_names:
            is_valid, error = validate_subreddit_name(name)
            assert not is_valid, f"'{name}' should be invalid"

    def test_reserved_names(self):
        """Test reserved names."""
        is_valid, error = validate_subreddit_name("admin")
        assert not is_valid
        assert "reserved" in error.lower()


class TestValidateCollectionConfig:
    """Tests for collection config validation."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = {
            "posts_limit": 100,
            "comments_limit": 50,
            "sort_methods": ["hot", "top", "new"],
            "time_filter": "week",
        }
        is_valid, errors = validate_collection_config(config)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_posts_limit(self):
        """Test invalid posts_limit values."""
        config = {"posts_limit": -1}
        is_valid, errors = validate_collection_config(config)
        assert not is_valid
        assert any("posts_limit" in e for e in errors)

    def test_invalid_sort_methods(self):
        """Test invalid sort methods."""
        config = {"sort_methods": ["invalid"]}
        is_valid, errors = validate_collection_config(config)
        assert not is_valid
        assert any("sort" in e.lower() for e in errors)

    def test_invalid_time_filter(self):
        """Test invalid time filter."""
        config = {"time_filter": "invalid"}
        is_valid, errors = validate_collection_config(config)
        assert not is_valid


class TestValidateRunId:
    """Tests for run ID validation."""

    def test_valid_run_id(self):
        """Test valid run IDs."""
        is_valid, _ = validate_run_id(1)
        assert is_valid

        is_valid, _ = validate_run_id(100)
        assert is_valid

    def test_none_run_id(self):
        """Test None run ID."""
        is_valid, error = validate_run_id(None)
        assert not is_valid

    def test_negative_run_id(self):
        """Test negative run ID."""
        is_valid, error = validate_run_id(-1)
        assert not is_valid

    def test_non_integer_run_id(self):
        """Test non-integer run ID."""
        is_valid, error = validate_run_id("1")
        assert not is_valid


class TestSanitizeText:
    """Tests for text sanitization."""

    def test_normal_text(self):
        """Test normal text."""
        text = "Hello, World!"
        result = sanitize_text(text)
        assert result == "Hello, World!"

    def test_null_bytes(self):
        """Test removal of null bytes."""
        text = "Hello\x00World"
        result = sanitize_text(text)
        assert "\x00" not in result

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        text = "Hello   World\n\nTest"
        result = sanitize_text(text)
        assert result == "Hello World Test"

    def test_truncation(self):
        """Test text truncation."""
        text = "a" * 20000
        result = sanitize_text(text, max_length=100)
        assert len(result) == 100

    def test_empty_text(self):
        """Test empty text."""
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""
