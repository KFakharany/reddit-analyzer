"""Main LangGraph workflow assembly."""

from typing import Any, Optional

from langgraph.graph import StateGraph, END

from src.state import WorkflowState, AnalysisPhase, WorkflowStatus, create_initial_state
from src.database import get_db_manager
from src.database.repositories import CommunityRepository, PostRepository, CommentRepository, AnalysisRepository

from src.workflow.nodes.collection import (
    fetch_posts_node,
    fetch_comments_node,
    store_to_db_node,
)
from src.workflow.nodes.extraction import (
    extract_scores_node,
    extract_flairs_node,
    extract_timing_node,
    extract_titles_node,
    extract_engagement_node,
    extract_audience_node,
    merge_extraction_node,
)
from src.workflow.nodes.analysis import (
    analyze_sentiment_node,
    analyze_pain_points_node,
    analyze_tone_node,
    analyze_promotion_node,
    merge_analysis_node,
)
from src.workflow.nodes.synthesis import (
    generate_personas_node,
    generate_insights_node,
    generate_report_node,
)
from src.workflow.routing import (
    should_collect_data,
    should_run_ai,
    check_for_errors,
)


def init_node(state: WorkflowState) -> dict[str, Any]:
    """Initialize the workflow.

    Validates input and sets up initial state.

    Args:
        state: Current workflow state.

    Returns:
        State update with initialization results.
    """
    community_name = state.get("community_name", "")

    if not community_name:
        return {
            "status": WorkflowStatus.FAILED,
            "error": "No community name provided",
        }

    # Check database connection
    db = get_db_manager()
    if not db.check_connection():
        return {
            "status": WorkflowStatus.FAILED,
            "error": "Database connection failed",
        }

    return {
        "status": WorkflowStatus.RUNNING,
        "phase": AnalysisPhase.INIT,
    }


def load_existing_data_node(state: WorkflowState) -> dict[str, Any]:
    """Load data from an existing collection run.

    Args:
        state: Current workflow state.

    Returns:
        State update with loaded data.
    """
    existing_run_id = state.get("existing_run_id")
    community_name = state.get("community_name")

    db = get_db_manager()

    try:
        with db.session() as session:
            community_repo = CommunityRepository(session)
            post_repo = PostRepository(session)
            comment_repo = CommentRepository(session)

            # Get or find the collection run
            if existing_run_id:
                run = community_repo.get_collection_run(existing_run_id)
                if not run:
                    return {"error": f"Collection run {existing_run_id} not found"}
            else:
                community = community_repo.get_by_name(community_name)
                if not community:
                    return {"error": f"Community {community_name} not found"}

                run = community_repo.get_latest_collection_run(community.id)
                if not run:
                    return {"error": f"No collection runs found for {community_name}"}

            # Load posts
            posts_db = post_repo.get_by_collection_run(run.id)
            posts = [
                {
                    "reddit_id": p.reddit_id,
                    "title": p.title,
                    "selftext": p.selftext,
                    "author_name": p.author_name,
                    "score": p.score,
                    "upvote_ratio": p.upvote_ratio,
                    "num_comments": p.num_comments,
                    "flair_text": p.flair_text,
                    "is_self": p.is_self,
                    "is_video": p.is_video,
                    "permalink": p.permalink,
                    "created_utc": p.created_utc,
                }
                for p in posts_db
            ]

            # Load comments
            comments_db = comment_repo.get_by_collection_run(run.id)
            comments = [
                {
                    "reddit_id": c.reddit_id,
                    "post_reddit_id": c.post.reddit_id if c.post else None,
                    "parent_reddit_id": c.parent_reddit_id,
                    "author_name": c.author_name,
                    "body": c.body,
                    "score": c.score,
                    "depth": c.depth,
                    "is_submitter": c.is_submitter,
                    "created_utc": c.created_utc,
                }
                for c in comments_db
            ]

            # Top items
            top_posts = posts[:20]
            top_comments = sorted(comments, key=lambda c: c.get("score", 0), reverse=True)[:50]

            # Community info
            community = run.community
            community_info = {
                "name": community.name,
                "display_name": community.display_name,
                "description": community.description,
                "subscribers": community.subscribers,
                "community_id": community.id,
            }

            return {
                "collection_run_id": run.id,
                "community_id": community.id,
                "community_info": community_info,
                "posts": posts,
                "comments": comments,
                "top_posts": top_posts,
                "top_comments": top_comments,
                "posts_collected": len(posts),
                "comments_collected": len(comments),
                "phase": AnalysisPhase.EXTRACTING,
            }

    except Exception as e:
        return {"error": f"Failed to load existing data: {str(e)}"}


def save_analysis_node(state: WorkflowState) -> dict[str, Any]:
    """Save analysis results to database.

    Args:
        state: Current workflow state.

    Returns:
        State update confirming save.
    """
    collection_run_id = state.get("collection_run_id")
    extraction_results = state.get("extraction_results", {})
    ai_analysis = state.get("ai_analysis", {})
    synthesis = state.get("synthesis", {})

    if not collection_run_id:
        return {}

    db = get_db_manager()

    try:
        with db.session() as session:
            analysis_repo = AnalysisRepository(session)

            # Save extraction results
            analysis_repo.create_analysis_result(
                collection_run_id=collection_run_id,
                score_distribution=extraction_results.get("score_distribution"),
                flair_distribution=extraction_results.get("flair_distribution"),
                timing_patterns=extraction_results.get("timing_patterns"),
                title_analysis=extraction_results.get("title_analysis"),
                op_engagement_analysis=extraction_results.get("op_engagement_analysis"),
                upvote_ratio_analysis=extraction_results.get("upvote_ratio_analysis"),
                post_format_analysis=extraction_results.get("post_format_analysis"),
            )

            # Save AI analysis
            analysis_repo.update_ai_analysis(
                collection_run_id=collection_run_id,
                sentiment_analysis=ai_analysis.get("sentiment_analysis"),
                pain_point_analysis=ai_analysis.get("pain_point_analysis"),
                tone_analysis=ai_analysis.get("tone_analysis"),
                promotion_analysis=ai_analysis.get("promotion_analysis"),
            )

            # Save audience analysis
            audience = extraction_results.get("audience_extraction", {})
            analysis_repo.create_audience_analysis(
                collection_run_id=collection_run_id,
                self_identifications=audience.get("self_identifications"),
                skill_levels=audience.get("skill_levels"),
                tools_mentioned=audience.get("tools_mentioned"),
                budget_signals=audience.get("budget_signals"),
                pain_points=audience.get("pain_points"),
                skepticism_level=audience.get("skepticism_level"),
                personas={"personas": synthesis.get("personas", [])},
            )

            # Save report
            report_content = synthesis.get("report_content", "")
            if report_content:
                analysis_repo.create_report(
                    collection_run_id=collection_run_id,
                    report_type="community_summary",
                    content=report_content,
                    report_metadata={
                        "insights_count": len(synthesis.get("insights", [])),
                        "personas_count": len(synthesis.get("personas", [])),
                    },
                )

        return {}

    except Exception as e:
        return {"errors": [f"Failed to save analysis: {str(e)}"]}


def output_node(state: WorkflowState) -> dict[str, Any]:
    """Final output node.

    Saves results and finalizes the workflow.

    Args:
        state: Current workflow state.

    Returns:
        Final state update.
    """
    # Save analysis to database
    save_result = save_analysis_node(state)

    errors = state.get("errors", []) + save_result.get("errors", [])

    return {
        "status": WorkflowStatus.COMPLETED if not state.get("error") else WorkflowStatus.FAILED,
        "phase": AnalysisPhase.DONE,
        "errors": errors,
    }


def error_node(state: WorkflowState) -> dict[str, Any]:
    """Handle workflow errors.

    Args:
        state: Current workflow state.

    Returns:
        Error state update.
    """
    return {
        "status": WorkflowStatus.FAILED,
        "phase": AnalysisPhase.DONE,
    }


def _merge_extraction_results(state: WorkflowState) -> dict[str, Any]:
    """Merge results from parallel extraction nodes.

    This is a helper that combines extraction results from the state.
    """
    return merge_extraction_node(state)


def _merge_analysis_results(state: WorkflowState) -> dict[str, Any]:
    """Merge results from parallel analysis nodes.

    This is a helper that combines AI analysis results from the state.
    """
    return merge_analysis_node(state)


def create_workflow() -> StateGraph:
    """Create the main analysis workflow graph.

    Returns:
        Configured StateGraph ready for execution.
    """
    # Create the graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("init", init_node)
    workflow.add_node("fetch_posts", fetch_posts_node)
    workflow.add_node("fetch_comments", fetch_comments_node)
    workflow.add_node("store_to_db", store_to_db_node)
    workflow.add_node("load_existing", load_existing_data_node)

    # Extraction nodes
    workflow.add_node("extract_scores", extract_scores_node)
    workflow.add_node("extract_flairs", extract_flairs_node)
    workflow.add_node("extract_timing", extract_timing_node)
    workflow.add_node("extract_titles", extract_titles_node)
    workflow.add_node("extract_engagement", extract_engagement_node)
    workflow.add_node("extract_audience", extract_audience_node)
    workflow.add_node("merge_extraction", _merge_extraction_results)

    # Analysis nodes
    workflow.add_node("analyze_sentiment", analyze_sentiment_node)
    workflow.add_node("analyze_pain_points", analyze_pain_points_node)
    workflow.add_node("analyze_tone", analyze_tone_node)
    workflow.add_node("analyze_promotion", analyze_promotion_node)
    workflow.add_node("merge_analysis", _merge_analysis_results)

    # Synthesis nodes
    workflow.add_node("generate_personas", generate_personas_node)
    workflow.add_node("generate_insights", generate_insights_node)
    workflow.add_node("generate_report", generate_report_node)

    # Output nodes
    workflow.add_node("output", output_node)
    workflow.add_node("error", error_node)

    # Set entry point
    workflow.set_entry_point("init")

    # Add edges from init
    workflow.add_conditional_edges(
        "init",
        check_for_errors,
        {
            "continue": "check_collection",
            "abort": "error",
        },
    )

    # Add a routing node for collection decision
    def check_collection_node(state: WorkflowState) -> dict[str, Any]:
        return {}

    workflow.add_node("check_collection", check_collection_node)

    workflow.add_conditional_edges(
        "check_collection",
        should_collect_data,
        {
            "collect": "fetch_posts",
            "load_existing": "load_existing",
        },
    )

    # Collection flow
    workflow.add_edge("fetch_posts", "fetch_comments")
    workflow.add_edge("fetch_comments", "store_to_db")
    workflow.add_edge("store_to_db", "extract_scores")
    workflow.add_edge("load_existing", "extract_scores")

    # Extraction flow (sequential for simplicity, can be parallelized)
    workflow.add_edge("extract_scores", "extract_flairs")
    workflow.add_edge("extract_flairs", "extract_timing")
    workflow.add_edge("extract_timing", "extract_titles")
    workflow.add_edge("extract_titles", "extract_engagement")
    workflow.add_edge("extract_engagement", "extract_audience")
    workflow.add_edge("extract_audience", "merge_extraction")

    # Add routing node for AI decision
    def check_ai_node(state: WorkflowState) -> dict[str, Any]:
        return {}

    workflow.add_node("check_ai", check_ai_node)

    workflow.add_edge("merge_extraction", "check_ai")

    workflow.add_conditional_edges(
        "check_ai",
        should_run_ai,
        {
            "analyze": "analyze_sentiment",
            "skip_to_output": "output",
        },
    )

    # Analysis flow (sequential for simplicity)
    workflow.add_edge("analyze_sentiment", "analyze_pain_points")
    workflow.add_edge("analyze_pain_points", "analyze_tone")
    workflow.add_edge("analyze_tone", "analyze_promotion")
    workflow.add_edge("analyze_promotion", "merge_analysis")

    # Synthesis flow (sequential - each depends on previous)
    workflow.add_edge("merge_analysis", "generate_personas")
    workflow.add_edge("generate_personas", "generate_insights")
    workflow.add_edge("generate_insights", "generate_report")
    workflow.add_edge("generate_report", "output")

    # Terminal edges
    workflow.add_edge("output", END)
    workflow.add_edge("error", END)

    return workflow


def run_analysis(
    community_name: str,
    skip_ai: bool = False,
    skip_collection: bool = False,
    existing_run_id: Optional[int] = None,
    output_dir: str = "./output",
    posts_limit: int = 100,
    comments_limit: int = 50,
) -> WorkflowState:
    """Run the complete analysis workflow.

    Args:
        community_name: Name of the subreddit to analyze.
        skip_ai: Skip AI analysis steps.
        skip_collection: Skip data collection (use existing data).
        existing_run_id: Existing collection run to analyze.
        output_dir: Directory for output files.
        posts_limit: Maximum posts to collect.
        comments_limit: Maximum comments per post.

    Returns:
        Final workflow state with results.
    """
    # Create initial state
    initial_state = create_initial_state(
        community_name=community_name,
        skip_ai=skip_ai,
        skip_collection=skip_collection,
        existing_run_id=existing_run_id,
        output_dir=output_dir,
        posts_limit=posts_limit,
        comments_limit=comments_limit,
    )

    # Create and compile workflow
    workflow = create_workflow()
    app = workflow.compile()

    # Run workflow and accumulate all state updates
    accumulated_state = dict(initial_state)

    for state_update in app.stream(initial_state):
        # LangGraph returns {node_name: partial_state_update}
        if isinstance(state_update, dict):
            for node_name, node_output in state_update.items():
                if isinstance(node_output, dict):
                    # Merge node's state update into accumulated state
                    accumulated_state.update(node_output)

    return accumulated_state
