"""Dashboard data endpoints."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from fastapi import APIRouter, Query, Request
from sqlmodel import Session, col, select

from app.db.models import (
    AnalysisRun,
    Article,
    Comment,
    DailyReport,
    RiskInsight,
    SentimentResult,
    TopicSummary,
)
from app.db.session import create_database_engine

router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary(
    request: Request,
    report_date: date | None = Query(default=None),
) -> dict[str, Any]:
    settings = request.app.state.settings
    selected_date = report_date or date.today()
    engine = create_database_engine(settings)
    try:
        with Session(engine) as session:
            analysis_run = _latest_completed_analysis_run(session)
            reports = _reports_for_date(session, selected_date)
            if analysis_run is None:
                return {
                    "status": "empty",
                    "selected_date": selected_date.isoformat(),
                    "latest_analysis_run": None,
                    "metrics": {
                        "sentiment_total": 0,
                        "negative_sentiment_count": 0,
                        "risk_count": 0,
                        "highest_risk_score": 0.0,
                        "report_count": len(reports),
                    },
                    "sentiment_distribution": {},
                    "risks": [],
                    "topics": [],
                    "evidence": [],
                    "reports": reports,
                }

            sentiments = session.exec(
                select(SentimentResult).where(SentimentResult.analysis_run_id == analysis_run.id)
            ).all()
            risks = session.exec(
                select(RiskInsight).where(RiskInsight.analysis_run_id == analysis_run.id)
            ).all()
            topics = session.exec(
                select(TopicSummary).where(TopicSummary.analysis_run_id == analysis_run.id)
            ).all()

            risks = sorted(risks, key=lambda risk: risk.deterministic_score, reverse=True)
            topics = sorted(topics, key=lambda topic: topic.growth_score, reverse=True)
            evidence = _evidence_for_ids(session, _collect_evidence_ids(risks, topics, sentiments))
            distribution = Counter(sentiment.label for sentiment in sentiments)
            highest_risk_score = risks[0].deterministic_score if risks else 0.0

            return {
                "status": "ok",
                "selected_date": selected_date.isoformat(),
                "latest_analysis_run": {
                    "id": analysis_run.id,
                    "status": analysis_run.status,
                    "provider": analysis_run.provider,
                    "model_name": analysis_run.model_name,
                    "mock_mode": analysis_run.mock_mode,
                    "created_at": analysis_run.created_at.isoformat(),
                    "runtime_metadata": analysis_run.runtime_metadata,
                },
                "metrics": {
                    "sentiment_total": len(sentiments),
                    "negative_sentiment_count": distribution.get("negative", 0),
                    "risk_count": len(risks),
                    "highest_risk_score": highest_risk_score,
                    "report_count": len(reports),
                },
                "sentiment_distribution": dict(distribution),
                "risks": [
                    {
                        "id": risk.id,
                        "category": risk.category,
                        "severity": risk.severity,
                        "deterministic_score": risk.deterministic_score,
                        "uncertainty_score": risk.uncertainty_score,
                        "explanation": risk.llm_explanation,
                        "evidence_ids": risk.evidence_ids,
                    }
                    for risk in risks
                ],
                "topics": [
                    {
                        "id": topic.id,
                        "topic": topic.topic,
                        "summary": topic.summary,
                        "keywords": topic.keywords,
                        "growth_score": topic.growth_score,
                        "trend_explanation": topic.trend_explanation,
                        "evidence_ids": topic.evidence_ids,
                    }
                    for topic in topics
                ],
                "evidence": evidence,
                "reports": reports,
            }
    finally:
        engine.dispose()


def _latest_completed_analysis_run(session: Session) -> AnalysisRun | None:
    statement = (
        select(AnalysisRun)
        .where(AnalysisRun.status == "completed")
        .order_by(col(AnalysisRun.created_at).desc())
    )
    return session.exec(statement).first()


def _reports_for_date(session: Session, selected_date: date) -> list[dict[str, Any]]:
    reports = session.exec(
        select(DailyReport)
        .where(DailyReport.report_date == selected_date)
        .order_by(col(DailyReport.created_at).desc())
    ).all()
    return [
        {
            "id": report.id,
            "title": report.title,
            "status": report.status,
            "summary": report.summary,
            "markdown_path": report.markdown_path,
            "html_path": report.html_path,
            "pdf_path": report.pdf_path,
            "analysis_run_ids": report.analysis_run_ids,
            "created_at": report.created_at.isoformat(),
        }
        for report in reports
    ]


def _collect_evidence_ids(*record_groups) -> set[str]:
    evidence_ids: set[str] = set()
    for record_group in record_groups:
        for record in record_group:
            evidence_ids.update(record.evidence_ids or [])
    return evidence_ids


def _evidence_for_ids(session: Session, evidence_ids: set[str]) -> list[dict[str, Any]]:
    if not evidence_ids:
        return []
    articles = session.exec(select(Article).where(col(Article.id).in_(evidence_ids))).all()
    comments = session.exec(select(Comment).where(col(Comment.id).in_(evidence_ids))).all()
    evidence = [
        {
            "id": article.id,
            "entity_type": "article",
            "title": article.title,
            "text": _truncate(article.cleaned_text or article.raw_text),
            "engagement_score": int(article.engagement.get("views", 0))
            + int(article.engagement.get("shares", 0)),
        }
        for article in articles
    ]
    evidence.extend(
        {
            "id": comment.id,
            "entity_type": "comment",
            "title": None,
            "text": _truncate(comment.cleaned_text or comment.raw_text),
            "engagement_score": comment.like_count + comment.reply_count + comment.share_count,
        }
        for comment in comments
    )
    evidence.sort(key=lambda item: item["engagement_score"], reverse=True)
    return evidence[:10]


def _truncate(text: str, limit: int = 220) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."
