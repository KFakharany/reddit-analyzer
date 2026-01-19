"""Node for extracting engagement patterns."""

from typing import Any

from src.state import WorkflowState


def extract_engagement_node(state: WorkflowState) -> dict[str, Any]:
    """Extract engagement patterns from posts and comments.

    This is a SCRIPT node - no AI involved.
    Analyzes OP engagement, upvote ratios, and comment patterns.

    Args:
        state: Current workflow state.

    Returns:
        State update with engagement analysis.
    """
    posts = state.get("posts", [])
    comments = state.get("comments", [])

    if not posts:
        return {
            "extraction_results": {
                "op_engagement_analysis": {},
                "upvote_ratio_analysis": {},
                "post_format_analysis": {},
            }
        }

    # OP Engagement Analysis
    op_comments = [c for c in comments if c.get("is_submitter", False)]
    posts_with_op_replies = set()
    for comment in op_comments:
        posts_with_op_replies.add(comment.get("post_reddit_id"))

    op_engagement = {
        "total_op_comments": len(op_comments),
        "posts_with_op_replies": len(posts_with_op_replies),
        "op_engagement_rate": round(
            len(posts_with_op_replies) / len(posts) * 100, 1
        ) if posts else 0,
        "avg_op_comment_score": round(
            sum(c.get("score", 0) for c in op_comments) / len(op_comments), 2
        ) if op_comments else 0,
    }

    # Upvote Ratio Analysis
    ratios = [p.get("upvote_ratio", 0.5) for p in posts if p.get("upvote_ratio")]
    scores = [p.get("score", 0) for p in posts]

    # Group by upvote ratio ranges
    ratio_buckets = {
        "controversial (0.5-0.6)": {"count": 0, "scores": []},
        "mixed (0.6-0.7)": {"count": 0, "scores": []},
        "positive (0.7-0.8)": {"count": 0, "scores": []},
        "well_received (0.8-0.9)": {"count": 0, "scores": []},
        "excellent (0.9+)": {"count": 0, "scores": []},
    }

    for i, post in enumerate(posts):
        ratio = post.get("upvote_ratio", 0.5)
        score = post.get("score", 0)

        if ratio < 0.6:
            ratio_buckets["controversial (0.5-0.6)"]["count"] += 1
            ratio_buckets["controversial (0.5-0.6)"]["scores"].append(score)
        elif ratio < 0.7:
            ratio_buckets["mixed (0.6-0.7)"]["count"] += 1
            ratio_buckets["mixed (0.6-0.7)"]["scores"].append(score)
        elif ratio < 0.8:
            ratio_buckets["positive (0.7-0.8)"]["count"] += 1
            ratio_buckets["positive (0.7-0.8)"]["scores"].append(score)
        elif ratio < 0.9:
            ratio_buckets["well_received (0.8-0.9)"]["count"] += 1
            ratio_buckets["well_received (0.8-0.9)"]["scores"].append(score)
        else:
            ratio_buckets["excellent (0.9+)"]["count"] += 1
            ratio_buckets["excellent (0.9+)"]["scores"].append(score)

    ratio_stats = {}
    for bucket_name, bucket_data in ratio_buckets.items():
        count = bucket_data["count"]
        bucket_scores = bucket_data["scores"]
        ratio_stats[bucket_name] = {
            "count": count,
            "percentage": round(count / len(posts) * 100, 1) if posts else 0,
            "avg_score": round(sum(bucket_scores) / len(bucket_scores), 2)
            if bucket_scores
            else 0,
        }

    upvote_analysis = {
        "avg_ratio": round(sum(ratios) / len(ratios), 3) if ratios else 0,
        "ratio_distribution": ratio_stats,
    }

    # Post Format Analysis
    self_posts = [p for p in posts if p.get("is_self", True)]
    link_posts = [p for p in posts if not p.get("is_self", True)]
    video_posts = [p for p in posts if p.get("is_video", False)]

    format_analysis = {
        "self_posts": {
            "count": len(self_posts),
            "percentage": round(len(self_posts) / len(posts) * 100, 1) if posts else 0,
            "avg_score": round(
                sum(p.get("score", 0) for p in self_posts) / len(self_posts), 2
            ) if self_posts else 0,
        },
        "link_posts": {
            "count": len(link_posts),
            "percentage": round(len(link_posts) / len(posts) * 100, 1) if posts else 0,
            "avg_score": round(
                sum(p.get("score", 0) for p in link_posts) / len(link_posts), 2
            ) if link_posts else 0,
        },
        "video_posts": {
            "count": len(video_posts),
            "percentage": round(len(video_posts) / len(posts) * 100, 1) if posts else 0,
            "avg_score": round(
                sum(p.get("score", 0) for p in video_posts) / len(video_posts), 2
            ) if video_posts else 0,
        },
    }

    # Comment depth analysis
    depth_counts = {}
    for comment in comments:
        depth = comment.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    return {
        "extraction_results": {
            "op_engagement_analysis": op_engagement,
            "upvote_ratio_analysis": upvote_analysis,
            "post_format_analysis": format_analysis,
        }
    }
