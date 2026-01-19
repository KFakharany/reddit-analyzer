"""Repository for Analysis data access."""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import AnalysisResult, AudienceAnalysis, Report


class AnalysisRepository:
    """Data access layer for analysis-related entities."""

    def __init__(self, session: Session):
        """Initialize with a database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    # AnalysisResult methods
    def get_analysis_result(self, collection_run_id: int) -> Optional[AnalysisResult]:
        """Get analysis result for a collection run.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            The AnalysisResult if found, None otherwise.
        """
        stmt = select(AnalysisResult).where(
            AnalysisResult.collection_run_id == collection_run_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_analysis_result(
        self,
        collection_run_id: int,
        score_distribution: Optional[dict[str, Any]] = None,
        flair_distribution: Optional[dict[str, Any]] = None,
        timing_patterns: Optional[dict[str, Any]] = None,
        title_analysis: Optional[dict[str, Any]] = None,
        op_engagement_analysis: Optional[dict[str, Any]] = None,
        upvote_ratio_analysis: Optional[dict[str, Any]] = None,
        post_format_analysis: Optional[dict[str, Any]] = None,
        author_success_analysis: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Create or update analysis result.

        Args:
            collection_run_id: The collection run ID.
            score_distribution: Score distribution data.
            flair_distribution: Flair distribution data.
            timing_patterns: Timing patterns data.
            title_analysis: Title analysis data.
            op_engagement_analysis: OP engagement data.
            upvote_ratio_analysis: Upvote ratio data.
            post_format_analysis: Post format data.
            author_success_analysis: Author success data.

        Returns:
            The AnalysisResult.
        """
        existing = self.get_analysis_result(collection_run_id)
        if existing:
            if score_distribution is not None:
                existing.score_distribution = score_distribution
            if flair_distribution is not None:
                existing.flair_distribution = flair_distribution
            if timing_patterns is not None:
                existing.timing_patterns = timing_patterns
            if title_analysis is not None:
                existing.title_analysis = title_analysis
            if op_engagement_analysis is not None:
                existing.op_engagement_analysis = op_engagement_analysis
            if upvote_ratio_analysis is not None:
                existing.upvote_ratio_analysis = upvote_ratio_analysis
            if post_format_analysis is not None:
                existing.post_format_analysis = post_format_analysis
            if author_success_analysis is not None:
                existing.author_success_analysis = author_success_analysis
            return existing

        result = AnalysisResult(
            collection_run_id=collection_run_id,
            score_distribution=score_distribution,
            flair_distribution=flair_distribution,
            timing_patterns=timing_patterns,
            title_analysis=title_analysis,
            op_engagement_analysis=op_engagement_analysis,
            upvote_ratio_analysis=upvote_ratio_analysis,
            post_format_analysis=post_format_analysis,
            author_success_analysis=author_success_analysis,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def update_ai_analysis(
        self,
        collection_run_id: int,
        sentiment_analysis: Optional[dict[str, Any]] = None,
        pain_point_analysis: Optional[dict[str, Any]] = None,
        tone_analysis: Optional[dict[str, Any]] = None,
        promotion_analysis: Optional[dict[str, Any]] = None,
    ) -> Optional[AnalysisResult]:
        """Update AI-generated analysis fields.

        Args:
            collection_run_id: The collection run ID.
            sentiment_analysis: Sentiment analysis data.
            pain_point_analysis: Pain point analysis data.
            tone_analysis: Tone analysis data.
            promotion_analysis: Promotion analysis data.

        Returns:
            The updated AnalysisResult or None if not found.
        """
        result = self.get_analysis_result(collection_run_id)
        if not result:
            result = self.create_analysis_result(collection_run_id)

        if sentiment_analysis is not None:
            result.sentiment_analysis = sentiment_analysis
        if pain_point_analysis is not None:
            result.pain_point_analysis = pain_point_analysis
        if tone_analysis is not None:
            result.tone_analysis = tone_analysis
        if promotion_analysis is not None:
            result.promotion_analysis = promotion_analysis

        return result

    # AudienceAnalysis methods
    def get_audience_analysis(
        self, collection_run_id: int
    ) -> Optional[AudienceAnalysis]:
        """Get audience analysis for a collection run.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            The AudienceAnalysis if found, None otherwise.
        """
        stmt = select(AudienceAnalysis).where(
            AudienceAnalysis.collection_run_id == collection_run_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_audience_analysis(
        self,
        collection_run_id: int,
        self_identifications: Optional[dict[str, Any]] = None,
        skill_levels: Optional[dict[str, Any]] = None,
        goals_motivations: Optional[dict[str, Any]] = None,
        pain_points: Optional[dict[str, Any]] = None,
        tools_mentioned: Optional[dict[str, Any]] = None,
        budget_signals: Optional[dict[str, Any]] = None,
        skepticism_level: Optional[str] = None,
        personas: Optional[dict[str, Any]] = None,
    ) -> AudienceAnalysis:
        """Create or update audience analysis.

        Args:
            collection_run_id: The collection run ID.
            self_identifications: Self-identification data.
            skill_levels: Skill level data.
            goals_motivations: Goals and motivations data.
            pain_points: Pain points data.
            tools_mentioned: Tools mentioned data.
            budget_signals: Budget signals data.
            skepticism_level: Skepticism level.
            personas: Personas data.

        Returns:
            The AudienceAnalysis.
        """
        existing = self.get_audience_analysis(collection_run_id)
        if existing:
            if self_identifications is not None:
                existing.self_identifications = self_identifications
            if skill_levels is not None:
                existing.skill_levels = skill_levels
            if goals_motivations is not None:
                existing.goals_motivations = goals_motivations
            if pain_points is not None:
                existing.pain_points = pain_points
            if tools_mentioned is not None:
                existing.tools_mentioned = tools_mentioned
            if budget_signals is not None:
                existing.budget_signals = budget_signals
            if skepticism_level is not None:
                existing.skepticism_level = skepticism_level
            if personas is not None:
                existing.personas = personas
            return existing

        analysis = AudienceAnalysis(
            collection_run_id=collection_run_id,
            self_identifications=self_identifications,
            skill_levels=skill_levels,
            goals_motivations=goals_motivations,
            pain_points=pain_points,
            tools_mentioned=tools_mentioned,
            budget_signals=budget_signals,
            skepticism_level=skepticism_level,
            personas=personas,
        )
        self.session.add(analysis)
        self.session.flush()
        return analysis

    # Report methods
    def get_report(
        self, collection_run_id: int, report_type: str
    ) -> Optional[Report]:
        """Get a report by collection run and type.

        Args:
            collection_run_id: The collection run ID.
            report_type: The type of report.

        Returns:
            The Report if found, None otherwise.
        """
        stmt = select(Report).where(
            Report.collection_run_id == collection_run_id,
            Report.report_type == report_type,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_report(
        self,
        collection_run_id: int,
        report_type: str,
        content: str,
        report_metadata: Optional[dict[str, Any]] = None,
    ) -> Report:
        """Create a new report.

        Args:
            collection_run_id: The collection run ID.
            report_type: The type of report.
            content: Report content (markdown).
            report_metadata: Additional metadata.

        Returns:
            The new Report.
        """
        report = Report(
            collection_run_id=collection_run_id,
            report_type=report_type,
            content=content,
            report_metadata=report_metadata,
        )
        self.session.add(report)
        self.session.flush()
        return report

    def list_reports(self, collection_run_id: int) -> list[Report]:
        """List all reports for a collection run.

        Args:
            collection_run_id: The collection run ID.

        Returns:
            List of Report objects.
        """
        stmt = (
            select(Report)
            .where(Report.collection_run_id == collection_run_id)
            .order_by(Report.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())
