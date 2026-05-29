from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import Article, Comment, DataQualityRecord, IngestionBatch  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402
from app.ingestion.contracts import IngestionPayload, RawArticle  # noqa: E402
from app.ingestion.local import LocalCSVConnector, LocalJSONConnector  # noqa: E402
from app.ingestion.rss import RSSConnector  # noqa: E402
from app.ingestion.service import IngestionService  # noqa: E402
from app.preprocessing.dedupe import build_content_hash  # noqa: E402
from app.preprocessing.language import detect_language  # noqa: E402
from app.preprocessing.pipeline import preprocess_article  # noqa: E402
from app.preprocessing.text import clean_text  # noqa: E402

SAMPLES = Path("data/samples")


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_preprocessing_cleans_detects_language_and_hashes_stably() -> None:
    article = RawArticle(
        external_id="raw-1",
        title=" 测试标题 ",
        raw_text="公共服务平台\n\n运行稳定，用户反馈较好，后续仍需持续观察高峰期表现。",
    )

    processed = preprocess_article(article)

    assert (
        clean_text(article.raw_text)
        == "公共服务平台 运行稳定，用户反馈较好，后续仍需持续观察高峰期表现。"
    )
    assert processed.language == "zh-CN"
    assert processed.content_hash == build_content_hash(None, article.title, processed.cleaned_text)
    assert processed.issues == []
    assert detect_language("plain English text") == "en"


def test_connectors_load_json_csv_and_rss_samples() -> None:
    json_payload = LocalJSONConnector(SAMPLES / "opinion_sample.json").load()
    csv_payload = LocalCSVConnector(SAMPLES / "local_articles.csv").load()
    rss_payload = RSSConnector(SAMPLES / "rss_sample.xml").load()

    assert json_payload.source_type == "local_json"
    assert len(json_payload.articles) == 1
    assert len(json_payload.comments) == 1
    assert csv_payload.source_type == "local_csv"
    assert len(csv_payload.articles) == 2
    assert rss_payload.source_type == "rss"
    assert rss_payload.articles[0].external_id == "rss-article-1"


def test_ingestion_service_persists_payload_and_skips_duplicates() -> None:
    with create_memory_session() as session:
        connector = LocalJSONConnector(SAMPLES / "opinion_sample.json")
        service = IngestionService(session)

        first = service.ingest(connector)
        second = service.ingest(connector)

        articles = session.exec(select(Article)).all()
        comments = session.exec(select(Comment)).all()
        batches = session.exec(select(IngestionBatch)).all()

        assert first.inserted_articles == 1
        assert first.inserted_comments == 1
        assert first.skipped_duplicate_articles == 0
        assert second.inserted_articles == 0
        assert second.inserted_comments == 0
        assert second.skipped_duplicate_articles == 1
        assert second.skipped_duplicate_comments == 1
        assert len(articles) == 1
        assert len(comments) == 1
        assert comments[0].article_id == articles[0].id
        assert len(batches) == 2


def test_ingestion_service_records_data_quality_issues() -> None:
    payload = IngestionPayload(
        source_name="quality-fixture",
        source_type="unit_test",
        articles=[
            RawArticle(
                external_id="short-article",
                title="短文本",
                raw_text="太短",
            )
        ],
    )

    with create_memory_session() as session:
        summary = IngestionService(session).ingest_payload(payload)
        quality_records = session.exec(select(DataQualityRecord)).all()

        assert summary.quality_issue_count == 1
        assert summary.quality_issues_by_severity == {"warning": 1}
        assert summary.quality_issues_by_type == {"short_text": 1}
        assert quality_records[0].issue_type == "short_text"
        assert quality_records[0].severity == "warning"
