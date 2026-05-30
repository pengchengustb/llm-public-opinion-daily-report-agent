"""Database-backed ingestion orchestration."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.db.models import (
    Article,
    Comment,
    DataQualityRecord,
    IngestionBatch,
    Source,
)
from app.db.repositories import (
    Repository,
    get_article_by_content_hash,
    get_comment_by_content_hash,
)
from app.ingestion.contracts import IngestionPayload, IngestionSummary, SourceConnector
from app.preprocessing.pipeline import preprocess_article, preprocess_comment
from app.preprocessing.quality import DataQualityIssue, summarize_quality_issues


class IngestionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ingest(self, connector: SourceConnector) -> IngestionSummary:
        return self.ingest_payload(connector.load())

    def ingest_payload(self, payload: IngestionPayload) -> IngestionSummary:
        source = self._get_or_create_source(payload)
        batch = Repository(self.session, IngestionBatch).add(
            IngestionBatch(
                source_id=source.id,
                status="running",
                connector_name=payload.source_type,
            )
        )

        inserted_articles = 0
        skipped_duplicate_articles = 0
        inserted_comments = 0
        skipped_duplicate_comments = 0
        error_issue_count = 0
        quality_issues: list[DataQualityIssue] = []
        article_ids_by_external_id: dict[str, str] = {}

        article_repo = Repository(self.session, Article)
        comment_repo = Repository(self.session, Comment)
        quality_repo = Repository(self.session, DataQualityRecord)

        for raw_article in payload.articles:
            processed = preprocess_article(raw_article)
            quality_issues.extend(processed.issues)
            self._persist_quality_issues(
                quality_repo,
                batch.id,
                processed.issues,
            )
            error_issue_count += sum(1 for issue in processed.issues if issue.severity == "error")
            existing = get_article_by_content_hash(self.session, processed.content_hash)
            if existing is not None:
                skipped_duplicate_articles += 1
                if raw_article.external_id:
                    article_ids_by_external_id[raw_article.external_id] = existing.id
                continue

            article = article_repo.add(
                Article(
                    source_id=source.id,
                    title=raw_article.title.strip(),
                    url=str(raw_article.url) if raw_article.url else None,
                    author=raw_article.author,
                    published_at=raw_article.published_at,
                    raw_text=raw_article.raw_text,
                    cleaned_text=processed.cleaned_text,
                    language=processed.language,
                    content_hash=processed.content_hash,
                    engagement=raw_article.engagement,
                )
            )
            inserted_articles += 1
            if raw_article.external_id:
                article_ids_by_external_id[raw_article.external_id] = article.id

        for raw_comment in payload.comments:
            processed_comment = preprocess_comment(raw_comment)
            quality_issues.extend(processed_comment.issues)
            self._persist_quality_issues(
                quality_repo,
                batch.id,
                processed_comment.issues,
            )
            error_issue_count += sum(
                1 for issue in processed_comment.issues if issue.severity == "error"
            )
            existing_comment = get_comment_by_content_hash(
                self.session,
                processed_comment.content_hash,
            )
            if existing_comment is not None:
                skipped_duplicate_comments += 1
                continue

            article_id = (
                article_ids_by_external_id.get(raw_comment.article_external_id)
                if raw_comment.article_external_id
                else None
            )
            comment_repo.add(
                Comment(
                    article_id=article_id,
                    platform=raw_comment.platform,
                    author_alias=raw_comment.author_alias,
                    published_at=raw_comment.published_at,
                    raw_text=raw_comment.raw_text,
                    cleaned_text=processed_comment.cleaned_text,
                    language=processed_comment.language,
                    content_hash=processed_comment.content_hash,
                    like_count=raw_comment.like_count,
                    reply_count=raw_comment.reply_count,
                    share_count=raw_comment.share_count,
                )
            )
            inserted_comments += 1

        batch.status = "completed"
        batch.finished_at = datetime.now(UTC)
        batch.article_count = inserted_articles
        batch.comment_count = inserted_comments
        batch.failure_count = error_issue_count
        self.session.add(batch)
        self.session.commit()
        quality_summary = summarize_quality_issues(quality_issues)

        return IngestionSummary(
            source_id=source.id,
            batch_id=batch.id,
            inserted_articles=inserted_articles,
            skipped_duplicate_articles=skipped_duplicate_articles,
            inserted_comments=inserted_comments,
            skipped_duplicate_comments=skipped_duplicate_comments,
            quality_issue_count=quality_summary.issue_count,
            quality_issues_by_severity=quality_summary.by_severity,
            quality_issues_by_type=quality_summary.by_type,
        )

    def _get_or_create_source(self, payload: IngestionPayload) -> Source:
        statement = select(Source).where(
            Source.name == payload.source_name,
            Source.source_type == payload.source_type,
            Source.uri == payload.uri,
        )
        existing = self.session.exec(statement).first()
        if existing is not None:
            return existing

        return Repository(self.session, Source).add(
            Source(
                name=payload.source_name,
                source_type=payload.source_type,
                uri=payload.uri,
                source_metadata=payload.metadata,
            )
        )

    def _persist_quality_issues(
        self,
        quality_repo: Repository[DataQualityRecord],
        batch_id: str,
        issues,
    ) -> None:
        for issue in issues:
            quality_repo.add(
                DataQualityRecord(
                    ingestion_batch_id=batch_id,
                    entity_type=issue.entity_type,
                    entity_id=issue.entity_id,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    message=issue.message,
                )
            )
