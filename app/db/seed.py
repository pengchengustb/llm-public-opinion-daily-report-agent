"""Seed helpers for deterministic local development samples."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session

from app.db.models import Article, Comment, Source
from app.db.repositories import (
    Repository,
    get_article_by_content_hash,
    get_comment_by_content_hash,
)

DEFAULT_SAMPLE_PATH = Path("data/samples/opinion_sample.json")


def load_sample_payload(path: Path = DEFAULT_SAMPLE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_sample_data(session: Session, path: Path = DEFAULT_SAMPLE_PATH) -> dict[str, int]:
    payload = load_sample_payload(path)
    source_repo = Repository(session, Source)
    article_repo = Repository(session, Article)
    comment_repo = Repository(session, Comment)

    source_payload = payload["source"]
    source = session.get(Source, source_payload["id"])
    inserted_sources = 0
    if source is None:
        source = source_repo.add(Source(**source_payload))
        inserted_sources = 1

    inserted_articles = 0
    inserted_comments = 0
    article_ids_by_external_id: dict[str, str] = {}

    for item in payload.get("articles", []):
        external_id = item.pop("external_id")
        item["published_at"] = parse_datetime(item.get("published_at"))
        existing = get_article_by_content_hash(session, item["content_hash"])
        if existing is None:
            article = article_repo.add(Article(source_id=source.id, **item))
            inserted_articles += 1
        else:
            article = existing
        article_ids_by_external_id[external_id] = article.id

    for item in payload.get("comments", []):
        article_external_id = item.pop("article_external_id")
        item["published_at"] = parse_datetime(item.get("published_at"))
        existing = get_comment_by_content_hash(session, item["content_hash"])
        if existing is None:
            comment_repo.add(
                Comment(
                    article_id=article_ids_by_external_id[article_external_id],
                    **item,
                )
            )
            inserted_comments += 1

    return {
        "inserted_sources": inserted_sources,
        "inserted_articles": inserted_articles,
        "inserted_comments": inserted_comments,
    }
