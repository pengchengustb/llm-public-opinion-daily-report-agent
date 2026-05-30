"""Validation and normalization pipeline for raw ingested records."""

from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.contracts import RawArticle, RawComment
from app.preprocessing.dedupe import build_content_hash
from app.preprocessing.language import detect_language
from app.preprocessing.quality import DataQualityIssue
from app.preprocessing.text import clean_text


@dataclass(frozen=True)
class ProcessedArticle:
    raw: RawArticle
    cleaned_text: str
    language: str
    content_hash: str
    issues: list[DataQualityIssue]


@dataclass(frozen=True)
class ProcessedComment:
    raw: RawComment
    cleaned_text: str
    language: str
    content_hash: str
    issues: list[DataQualityIssue]


def preprocess_article(article: RawArticle) -> ProcessedArticle:
    cleaned_text = clean_text(article.raw_text)
    issues: list[DataQualityIssue] = []
    if not article.title.strip():
        issues.append(
            DataQualityIssue(
                entity_type="article",
                entity_id=article.external_id,
                issue_type="missing_title",
                severity="error",
                message="Article title is empty.",
            )
        )
    if len(cleaned_text) < 20:
        issues.append(
            DataQualityIssue(
                entity_type="article",
                entity_id=article.external_id,
                issue_type="short_text",
                severity="warning",
                message="Article text is too short for reliable analysis.",
            )
        )

    return ProcessedArticle(
        raw=article,
        cleaned_text=cleaned_text,
        language=detect_language(cleaned_text),
        content_hash=build_content_hash(
            str(article.url) if article.url else None,
            article.title,
            cleaned_text,
        ),
        issues=issues,
    )


def preprocess_comment(comment: RawComment) -> ProcessedComment:
    cleaned_text = clean_text(comment.raw_text)
    issues: list[DataQualityIssue] = []
    if len(cleaned_text) < 3:
        issues.append(
            DataQualityIssue(
                entity_type="comment",
                entity_id=comment.external_id,
                issue_type="short_text",
                severity="warning",
                message="Comment text is too short for reliable analysis.",
            )
        )

    return ProcessedComment(
        raw=comment,
        cleaned_text=cleaned_text,
        language=detect_language(cleaned_text),
        content_hash=build_content_hash(comment.article_external_id, cleaned_text),
        issues=issues,
    )
