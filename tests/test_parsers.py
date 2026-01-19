"""Tests for Reddit API parsers."""

import pytest
from datetime import datetime

from src.reddit.parsers import (
    parse_timestamp,
    parse_post,
    parse_comment,
    parse_author,
    parse_subreddit_about,
    extract_post_listing,
)


class TestParseTimestamp:
    """Tests for timestamp parsing."""

    def test_valid_timestamp(self):
        """Test valid Unix timestamp."""
        result = parse_timestamp(1704067200)  # 2024-01-01 00:00:00
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_none_timestamp(self):
        """Test None timestamp."""
        assert parse_timestamp(None) is None


class TestParsePost:
    """Tests for post parsing."""

    def test_full_post_data(self):
        """Test parsing complete post data."""
        data = {
            "id": "abc123",
            "title": "Test Post Title",
            "selftext": "Post body text",
            "author": "test_user",
            "score": 100,
            "upvote_ratio": 0.95,
            "num_comments": 50,
            "link_flair_text": "Discussion",
            "is_self": True,
            "is_video": False,
            "permalink": "/r/test/comments/abc123/test_post/",
            "created_utc": 1704067200,
        }

        result = parse_post(data)

        assert result["reddit_id"] == "abc123"
        assert result["title"] == "Test Post Title"
        assert result["author_name"] == "test_user"
        assert result["score"] == 100
        assert result["flair_text"] == "Discussion"

    def test_minimal_post_data(self):
        """Test parsing minimal post data."""
        data = {"id": "xyz789", "title": "Minimal Post"}

        result = parse_post(data)

        assert result["reddit_id"] == "xyz789"
        assert result["title"] == "Minimal Post"
        assert result["selftext"] == ""
        assert result["score"] == 0


class TestParseComment:
    """Tests for comment parsing."""

    def test_valid_comment(self):
        """Test parsing valid comment."""
        data = {
            "kind": "t1",
            "data": {
                "id": "comment123",
                "body": "This is a comment",
                "author": "commenter",
                "score": 25,
                "parent_id": "t3_post123",
                "is_submitter": False,
                "created_utc": 1704067200,
            },
        }

        result = parse_comment(data, "post123")

        assert result["reddit_id"] == "comment123"
        assert result["body"] == "This is a comment"
        assert result["author_name"] == "commenter"
        assert result["score"] == 25
        assert not result["is_submitter"]

    def test_op_comment(self):
        """Test parsing OP comment."""
        data = {
            "kind": "t1",
            "data": {
                "id": "comment456",
                "body": "OP responding",
                "author": "op_user",
                "score": 50,
                "parent_id": "t3_post123",
                "is_submitter": True,
                "created_utc": 1704067200,
            },
        }

        result = parse_comment(data, "post123")

        assert result["is_submitter"] is True

    def test_deleted_comment(self):
        """Test parsing deleted comment returns None."""
        data = {
            "kind": "t1",
            "data": {
                "id": "deleted123",
                "body": "[deleted]",
                "author": "[deleted]",
            },
        }

        result = parse_comment(data, "post123")

        assert result is None

    def test_non_comment_kind(self):
        """Test non-comment type returns None."""
        data = {"kind": "more", "data": {}}

        result = parse_comment(data, "post123")

        assert result is None


class TestParseAuthor:
    """Tests for author parsing."""

    def test_full_author_data(self):
        """Test parsing complete author data."""
        data = {
            "data": {
                "name": "test_user",
                "link_karma": 1000,
                "comment_karma": 5000,
                "total_karma": 6000,
                "created_utc": 1600000000,
                "is_gold": True,
            }
        }

        result = parse_author(data)

        assert result["username"] == "test_user"
        assert result["link_karma"] == 1000
        assert result["comment_karma"] == 5000
        assert result["total_karma"] == 6000
        assert result["is_gold"] is True


class TestParseSubredditAbout:
    """Tests for subreddit about parsing."""

    def test_full_subreddit_data(self):
        """Test parsing complete subreddit data."""
        data = {
            "data": {
                "display_name": "TestSubreddit",
                "public_description": "A test subreddit",
                "subscribers": 100000,
            }
        }

        result = parse_subreddit_about(data)

        assert result["name"] == "TestSubreddit"
        assert result["display_name"] == "r/TestSubreddit"
        assert result["subscribers"] == 100000


class TestExtractPostListing:
    """Tests for post listing extraction."""

    def test_valid_listing(self):
        """Test extracting posts from listing."""
        response = {
            "data": {
                "children": [
                    {"kind": "t3", "data": {"id": "post1", "title": "Post 1"}},
                    {"kind": "t3", "data": {"id": "post2", "title": "Post 2"}},
                ]
            }
        }

        result = extract_post_listing(response)

        assert len(result) == 2
        assert result[0]["id"] == "post1"
        assert result[1]["id"] == "post2"

    def test_empty_listing(self):
        """Test empty listing."""
        response = {"data": {"children": []}}

        result = extract_post_listing(response)

        assert len(result) == 0
