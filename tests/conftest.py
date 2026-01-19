"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import MagicMock, patch


# Set test environment variables before importing app modules
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["ANTHROPIC_API_KEY"] = "test_key"


@pytest.fixture
def sample_post_data():
    """Sample Reddit post data."""
    return {
        "id": "test123",
        "title": "Test Post Title",
        "selftext": "This is the body of the test post.",
        "author": "test_author",
        "score": 150,
        "upvote_ratio": 0.92,
        "num_comments": 45,
        "link_flair_text": "Discussion",
        "is_self": True,
        "is_video": False,
        "permalink": "/r/test/comments/test123/test_post/",
        "created_utc": 1704067200,
    }


@pytest.fixture
def sample_comment_data():
    """Sample Reddit comment data."""
    return {
        "kind": "t1",
        "data": {
            "id": "comment123",
            "body": "This is a test comment with some content.",
            "author": "commenter",
            "score": 25,
            "parent_id": "t3_test123",
            "is_submitter": False,
            "created_utc": 1704067300,
        },
    }


@pytest.fixture
def sample_posts():
    """List of sample posts for testing."""
    return [
        {
            "reddit_id": f"post{i}",
            "title": f"Test Post {i}",
            "selftext": f"Body of post {i}",
            "author_name": f"author{i}",
            "score": 100 - i * 10,
            "upvote_ratio": 0.9 - i * 0.05,
            "num_comments": 50 - i * 5,
            "flair_text": ["Discussion", "Question", "Resource", None][i % 4],
            "is_self": True,
            "is_video": False,
            "created_utc": None,
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_comments():
    """List of sample comments for testing."""
    return [
        {
            "reddit_id": f"comment{i}",
            "post_reddit_id": f"post{i % 5}",
            "parent_reddit_id": None if i % 3 == 0 else f"comment{i - 1}",
            "author_name": f"commenter{i}",
            "body": f"This is comment {i} with some text.",
            "score": 50 - i * 3,
            "depth": i % 3,
            "is_submitter": i % 5 == 0,
            "created_utc": None,
        }
        for i in range(20)
    ]


@pytest.fixture
def mock_reddit_client():
    """Mock Reddit client for testing."""
    with patch("src.reddit.client.RedditClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__aenter__.return_value = client_instance

        # Set up default return values
        client_instance.get_subreddit_about.return_value = {
            "name": "TestSubreddit",
            "display_name": "r/TestSubreddit",
            "description": "A test subreddit",
            "subscribers": 100000,
        }

        yield client_instance


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    with patch("src.database.connection.DatabaseManager") as mock:
        session = MagicMock()
        mock.return_value.session.return_value.__enter__.return_value = session
        yield session


@pytest.fixture
def workflow_state():
    """Sample workflow state for testing."""
    from src.state import create_initial_state

    return create_initial_state(
        community_name="TestSubreddit",
        skip_ai=False,
        posts_limit=50,
        comments_limit=25,
    )


@pytest.fixture
def extraction_results():
    """Sample extraction results for testing."""
    return {
        "score_distribution": {
            "min": 0,
            "max": 1000,
            "avg": 150,
            "median": 100,
            "total_posts": 50,
            "buckets": {
                "0-10": 5,
                "11-50": 15,
                "51-100": 20,
                "101-500": 8,
                "501-1000": 2,
                "1000+": 0,
            },
        },
        "flair_distribution": {
            "flairs": {
                "Discussion": {"count": 20, "percentage": 40.0, "avg_score": 120},
                "Question": {"count": 15, "percentage": 30.0, "avg_score": 80},
                "Resource": {"count": 10, "percentage": 20.0, "avg_score": 200},
            },
            "no_flair_count": 5,
            "total_posts": 50,
        },
        "timing_patterns": {
            "best_hour": {"hour": "14:00", "avg_score": 180},
            "best_day": {"day": "Tuesday", "avg_score": 150},
        },
        "audience_extraction": {
            "self_identifications": {"developer": 10, "student": 5, "marketer": 3},
            "skill_levels": {"distribution": {"beginner": 20, "intermediate": 15, "advanced": 10}},
            "tools_mentioned": {"ChatGPT": 25, "Python": 15, "VS Code": 10},
            "skepticism_level": "medium",
        },
    }


@pytest.fixture
def ai_analysis_results():
    """Sample AI analysis results for testing."""
    return {
        "sentiment_analysis": {
            "overall_sentiment": "positive",
            "sentiment_distribution": {
                "positive": 60,
                "neutral": 30,
                "negative": 10,
            },
        },
        "pain_point_analysis": {
            "top_pain_points": [
                {"pain_point": "Learning curve", "who_experiences_it": "beginners"},
                {"pain_point": "Cost concerns", "who_experiences_it": "all users"},
            ],
        },
        "tone_analysis": {
            "overall_tone": {
                "formality": "casual",
                "friendliness": "friendly",
            },
        },
        "promotion_analysis": {
            "promotion_reception": {
                "overall_attitude": "tolerated",
            },
        },
    }
