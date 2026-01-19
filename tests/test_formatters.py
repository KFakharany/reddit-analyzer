"""Tests for formatting utilities."""

import pytest
from datetime import datetime, timedelta

from src.utils.formatters import (
    format_number,
    format_percentage,
    format_timestamp,
    truncate_text,
    format_karma,
    format_time_ago,
)


class TestFormatNumber:
    """Tests for number formatting."""

    def test_integer(self):
        """Test integer formatting."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"

    def test_float(self):
        """Test float formatting."""
        assert format_number(1234.56, precision=2) == "1,234.56"

    def test_small_number(self):
        """Test small numbers."""
        assert format_number(42) == "42"


class TestFormatPercentage:
    """Tests for percentage formatting."""

    def test_decimal_input(self):
        """Test with 0-1 range input."""
        assert format_percentage(0.5) == "50.0%"
        assert format_percentage(0.123) == "12.3%"

    def test_percentage_input(self):
        """Test with 0-100 range input."""
        assert format_percentage(50) == "50.0%"

    def test_precision(self):
        """Test precision control."""
        assert format_percentage(0.1234, precision=2) == "12.34%"


class TestFormatTimestamp:
    """Tests for timestamp formatting."""

    def test_valid_datetime(self):
        """Test valid datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = format_timestamp(dt)
        assert "2024-01-15" in result
        assert "10:30" in result

    def test_none_datetime(self):
        """Test None datetime."""
        assert format_timestamp(None) == "N/A"

    def test_custom_format(self):
        """Test custom format string."""
        dt = datetime(2024, 1, 15)
        result = format_timestamp(dt, "%Y/%m/%d")
        assert result == "2024/01/15"


class TestTruncateText:
    """Tests for text truncation."""

    def test_short_text(self):
        """Test text shorter than limit."""
        text = "Hello"
        result = truncate_text(text, max_length=100)
        assert result == "Hello"

    def test_long_text(self):
        """Test text longer than limit."""
        text = "a" * 200
        result = truncate_text(text, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_empty_text(self):
        """Test empty text."""
        assert truncate_text("") == ""

    def test_custom_suffix(self):
        """Test custom suffix."""
        text = "a" * 200
        result = truncate_text(text, max_length=100, suffix="[...]")
        assert result.endswith("[...]")


class TestFormatKarma:
    """Tests for karma formatting."""

    def test_small_karma(self):
        """Test small karma values."""
        assert format_karma(500) == "500"

    def test_thousands(self):
        """Test thousands."""
        assert format_karma(5000) == "5.0K"
        assert format_karma(15000) == "15.0K"

    def test_millions(self):
        """Test millions."""
        assert format_karma(5000000) == "5.0M"


class TestFormatTimeAgo:
    """Tests for relative time formatting."""

    def test_just_now(self):
        """Test very recent time."""
        dt = datetime.utcnow() - timedelta(seconds=30)
        result = format_time_ago(dt)
        assert result == "just now"

    def test_minutes_ago(self):
        """Test minutes ago."""
        dt = datetime.utcnow() - timedelta(minutes=5)
        result = format_time_ago(dt)
        assert "minute" in result

    def test_hours_ago(self):
        """Test hours ago."""
        dt = datetime.utcnow() - timedelta(hours=3)
        result = format_time_ago(dt)
        assert "hour" in result

    def test_days_ago(self):
        """Test days ago."""
        dt = datetime.utcnow() - timedelta(days=5)
        result = format_time_ago(dt)
        assert "day" in result
