"""Daily report assembly and export services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlmodel import Session, col, select

from app.core.config import Settings, get_settings
from app.db.models import (
    AnalysisRun,
    Article,
    Comment,
    DailyReport,
    Recommendation,
    RiskInsight,
    SentimentResult,
    TopicSummary,
    Viewpoint,
)


class ReportGenerationError(RuntimeError):
    """Base exception for report generation failures."""


class ReportTraceabilityError(ReportGenerationError):
    """Raised when report evidence IDs cannot be resolved."""


@dataclass(frozen=True)
class EvidenceSummary:
    evidence_id: str
    entity_type: str
    title: str | None
    text: str
    engagement_score: int


@dataclass(frozen=True)
class ReportArtifacts:
    report: DailyReport
    markdown_path: Path
    html_path: Path


@dataclass(frozen=True)
class ReportContext:
    report_date: date
    title: str
    summary: str
    analysis_run: AnalysisRun
    sentiments: list[SentimentResult]
    viewpoints: list[Viewpoint]
    topics: list[TopicSummary]
    risks: list[RiskInsight]
    recommendations: list[Recommendation]
    evidence: list[EvidenceSummary]

    @property
    def negative_sentiment_count(self) -> int:
        return sum(1 for sentiment in self.sentiments if sentiment.label == "negative")

    @property
    def average_risk_score(self) -> float:
        if not self.risks:
            return 0.0
        return round(sum(risk.deterministic_score for risk in self.risks) / len(self.risks), 2)


class ReportGenerationService:
    """Assemble traceable daily reports from persisted analysis outputs."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.output_dir = output_dir or self.settings.report_output_dir
        template_dir = Path(__file__).parent / "templates"
        self.templates = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_daily_report(
        self,
        report_date: date | None = None,
        analysis_run_id: str | None = None,
    ) -> ReportArtifacts:
        resolved_date = report_date or date.today()
        analysis_run = self._resolve_analysis_run(analysis_run_id)
        context = self._build_context(resolved_date, analysis_run)
        self._validate_traceability(context)

        report_dir = self.output_dir / resolved_date.isoformat()
        report_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = report_dir / f"daily_report_{resolved_date.isoformat()}.md"
        html_path = report_dir / f"daily_report_{resolved_date.isoformat()}.html"

        markdown = self.templates.get_template("daily_report.md.j2").render(context=context)
        html = self.templates.get_template("daily_report.html.j2").render(context=context)
        markdown_path.write_text(markdown, encoding="utf-8")
        html_path.write_text(html, encoding="utf-8")

        report = DailyReport(
            report_date=resolved_date,
            status="generated",
            title=context.title,
            summary=context.summary,
            markdown_path=str(markdown_path),
            html_path=str(html_path),
            analysis_run_ids=[analysis_run.id],
        )
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        return ReportArtifacts(report=report, markdown_path=markdown_path, html_path=html_path)

    def _resolve_analysis_run(self, analysis_run_id: str | None) -> AnalysisRun:
        if analysis_run_id:
            analysis_run = self.session.get(AnalysisRun, analysis_run_id)
            if analysis_run is None:
                raise ReportGenerationError(f"Analysis run not found: {analysis_run_id}")
            return analysis_run

        statement = (
            select(AnalysisRun)
            .where(AnalysisRun.status == "completed")
            .order_by(col(AnalysisRun.created_at).desc())
        )
        analysis_run = self.session.exec(statement).first()
        if analysis_run is None:
            raise ReportGenerationError("No completed analysis run is available for reporting.")
        return analysis_run

    def _build_context(self, report_date: date, analysis_run: AnalysisRun) -> ReportContext:
        sentiments = self._list_by_run(SentimentResult, analysis_run.id)
        viewpoints = self._list_by_run(Viewpoint, analysis_run.id)
        topics = self._list_by_run(TopicSummary, analysis_run.id)
        risks = self._list_by_run(RiskInsight, analysis_run.id)
        risks.sort(key=lambda risk: risk.deterministic_score, reverse=True)

        risk_ids = [risk.id for risk in risks]
        recommendations = self._list_recommendations(risk_ids)
        evidence = self._list_evidence(
            self._collect_evidence_ids(sentiments, viewpoints, topics, risks)
        )

        top_risk = risks[0] if risks else None
        summary = (
            f"Highest risk category {top_risk.category} scored "
            f"{top_risk.deterministic_score:.2f} with severity {top_risk.severity}."
            if top_risk
            else "No persisted risk insights were available for this report."
        )
        title = f"舆情风险日报 {report_date.isoformat()}"
        return ReportContext(
            report_date=report_date,
            title=title,
            summary=summary,
            analysis_run=analysis_run,
            sentiments=sentiments,
            viewpoints=viewpoints,
            topics=topics,
            risks=risks,
            recommendations=recommendations,
            evidence=evidence,
        )

    def _validate_traceability(self, context: ReportContext) -> None:
        known_ids = {item.evidence_id for item in context.evidence}
        referenced_ids = self._collect_evidence_ids(
            context.sentiments,
            context.viewpoints,
            context.topics,
            context.risks,
            context.recommendations,
        )
        missing_ids = sorted(referenced_ids - known_ids)
        if missing_ids:
            raise ReportTraceabilityError(
                "Report evidence traceability failed; missing evidence IDs: "
                + ", ".join(missing_ids)
            )

    def _list_recommendations(self, risk_ids: list[str]) -> list[Recommendation]:
        if not risk_ids:
            return []
        statement = select(Recommendation).where(col(Recommendation.risk_insight_id).in_(risk_ids))
        return list(self.session.exec(statement).all())

    def _list_evidence(self, evidence_ids: set[str]) -> list[EvidenceSummary]:
        if not evidence_ids:
            return []

        articles = self.session.exec(select(Article).where(col(Article.id).in_(evidence_ids))).all()
        comments = self.session.exec(select(Comment).where(col(Comment.id).in_(evidence_ids))).all()
        evidence = [
            EvidenceSummary(
                evidence_id=article.id,
                entity_type="article",
                title=article.title,
                text=self._truncate(article.cleaned_text or article.raw_text),
                engagement_score=int(article.engagement.get("views", 0))
                + int(article.engagement.get("shares", 0)),
            )
            for article in articles
        ]
        evidence.extend(
            EvidenceSummary(
                evidence_id=comment.id,
                entity_type="comment",
                title=None,
                text=self._truncate(comment.cleaned_text or comment.raw_text),
                engagement_score=comment.like_count + comment.reply_count + comment.share_count,
            )
            for comment in comments
        )
        evidence.sort(key=lambda item: item.engagement_score, reverse=True)
        return evidence

    def _collect_evidence_ids(self, *records) -> set[str]:
        evidence_ids: set[str] = set()
        for record_group in records:
            for record in record_group:
                evidence_ids.update(record.evidence_ids or [])
        return evidence_ids

    def _list_by_run(self, model, analysis_run_id: str):
        statement = select(model).where(model.analysis_run_id == analysis_run_id)
        return list(self.session.exec(statement).all())

    def _truncate(self, text: str, limit: int = 220) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3] + "..."
