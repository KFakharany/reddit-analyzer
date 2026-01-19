"""Parsers for Reddit JSON API responses."""

from datetime import datetime
from typing import Any, Optional


def parse_timestamp(utc_timestamp: Optional[float]) -> Optional[datetime]:
    """Convert Unix timestamp to datetime.

    Args:
        utc_timestamp: Unix timestamp from Reddit API.

    Returns:
        datetime object or None if timestamp is None.
    """
    if utc_timestamp is None:
        return None
    return datetime.utcfromtimestamp(utc_timestamp)


def parse_post(data: dict[str, Any]) -> dict[str, Any]:
    """Parse a post from Reddit JSON API response.

    Args:
        data: Raw post data from Reddit API (the 'data' field of a post listing).

    Returns:
        Parsed post dictionary ready for database insertion.
    """
    return {
        "reddit_id": data.get("id", ""),
        "title": data.get("title", ""),
        "selftext": data.get("selftext", ""),
        "author_name": data.get("author"),
        "score": data.get("score", 0),
        "upvote_ratio": data.get("upvote_ratio"),
        "num_comments": data.get("num_comments", 0),
        "flair_text": data.get("link_flair_text"),
        "is_self": data.get("is_self", True),
        "is_video": data.get("is_video", False),
        "permalink": data.get("permalink", ""),
        "created_utc": parse_timestamp(data.get("created_utc")),
    }


def parse_comment(
    data: dict[str, Any],
    post_reddit_id: str,
    depth: int = 0,
) -> Optional[dict[str, Any]]:
    """Parse a comment from Reddit JSON API response.

    Args:
        data: Raw comment data from Reddit API.
        post_reddit_id: Reddit ID of the parent post.
        depth: Nesting depth of the comment.

    Returns:
        Parsed comment dictionary or None if not a valid comment.
    """
    # Skip non-comment entries (like "more" links)
    if data.get("kind") != "t1":
        return None

    comment_data = data.get("data", {})

    # Skip deleted/removed comments with no content
    body = comment_data.get("body", "")
    if body in ("[deleted]", "[removed]", ""):
        return None

    # Determine parent: if parent_id starts with t3_, it's the post
    parent_id = comment_data.get("parent_id", "")
    parent_reddit_id = None
    if parent_id.startswith("t1_"):
        parent_reddit_id = parent_id[3:]  # Remove "t1_" prefix

    return {
        "reddit_id": comment_data.get("id", ""),
        "parent_reddit_id": parent_reddit_id,
        "author_name": comment_data.get("author"),
        "body": body,
        "score": comment_data.get("score", 0),
        "depth": depth,
        "is_submitter": comment_data.get("is_submitter", False),
        "created_utc": parse_timestamp(comment_data.get("created_utc")),
    }


def parse_comments_tree(
    data: list[dict[str, Any]],
    post_reddit_id: str,
    depth: int = 0,
    max_depth: int = 10,
) -> list[dict[str, Any]]:
    """Recursively parse a comment tree.

    Args:
        data: List of comment data from Reddit API.
        post_reddit_id: Reddit ID of the parent post.
        depth: Current nesting depth.
        max_depth: Maximum depth to traverse.

    Returns:
        Flattened list of parsed comments.
    """
    comments = []

    for item in data:
        if item.get("kind") == "t1":
            parsed = parse_comment(item, post_reddit_id, depth)
            if parsed:
                comments.append(parsed)

                # Recursively parse replies
                if depth < max_depth:
                    replies_data = item.get("data", {}).get("replies")
                    if replies_data and isinstance(replies_data, dict):
                        children = replies_data.get("data", {}).get("children", [])
                        comments.extend(
                            parse_comments_tree(
                                children,
                                post_reddit_id,
                                depth + 1,
                                max_depth,
                            )
                        )

    return comments


def parse_author(data: dict[str, Any]) -> dict[str, Any]:
    """Parse author data from Reddit JSON API response.

    Args:
        data: Raw author data from Reddit API (from /user/{name}/about.json).

    Returns:
        Parsed author dictionary ready for database insertion.
    """
    author_data = data.get("data", data)

    return {
        "username": author_data.get("name", ""),
        "link_karma": author_data.get("link_karma", 0),
        "comment_karma": author_data.get("comment_karma", 0),
        "total_karma": author_data.get("total_karma", 0),
        "account_created_utc": parse_timestamp(author_data.get("created_utc")),
        "is_gold": author_data.get("is_gold", False),
    }


def parse_subreddit_about(data: dict[str, Any]) -> dict[str, Any]:
    """Parse subreddit about data from Reddit JSON API response.

    Args:
        data: Raw subreddit data from Reddit API (from /r/{sub}/about.json).

    Returns:
        Parsed subreddit dictionary.
    """
    sub_data = data.get("data", data)

    return {
        "name": sub_data.get("display_name", ""),
        "display_name": f"r/{sub_data.get('display_name', '')}",
        "description": sub_data.get("public_description", ""),
        "subscribers": sub_data.get("subscribers", 0),
    }


def extract_post_listing(response_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract posts from a listing response.

    Args:
        response_data: Raw response from Reddit API listing endpoint.

    Returns:
        List of raw post data dictionaries.
    """
    posts = []
    children = response_data.get("data", {}).get("children", [])

    for child in children:
        if child.get("kind") == "t3":  # t3 = post/link
            posts.append(child.get("data", {}))

    return posts


def extract_comments_from_post_page(
    response_data: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract post and comments from a post page response.

    The post page response is a list with two elements:
    1. The post listing (single post)
    2. The comments listing

    Args:
        response_data: Raw response from Reddit post page endpoint.

    Returns:
        Tuple of (post_data, list of comment data).
    """
    if len(response_data) < 2:
        return {}, []

    # First element is the post
    post_listing = response_data[0]
    post_children = post_listing.get("data", {}).get("children", [])
    post_data = post_children[0].get("data", {}) if post_children else {}

    # Second element is the comments
    comments_listing = response_data[1]
    comments_children = comments_listing.get("data", {}).get("children", [])

    return post_data, comments_children
