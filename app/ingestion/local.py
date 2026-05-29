"""Local JSON and CSV source connectors."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.ingestion.contracts import IngestionPayload, RawArticle, RawComment


class LocalJSONConnector:
    source_type = "local_json"

    def __init__(self, path: str | Path, name: str | None = None) -> None:
        self.path = Path(path)
        self.name = name or self.path.stem
        self.uri = str(self.path)

    def load(self) -> IngestionPayload:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            articles = payload
            comments = []
            source = {}
        else:
            articles = payload.get("articles", [])
            comments = payload.get("comments", [])
            source = payload.get("source", {})

        return IngestionPayload(
            source_name=source.get("name", self.name),
            source_type=source.get("source_type", self.source_type),
            uri=source.get("uri", self.uri),
            articles=[RawArticle(**_strip_article_fields(item)) for item in articles],
            comments=[RawComment(**_strip_comment_fields(item)) for item in comments],
            metadata=source.get("source_metadata", {}),
        )


class LocalCSVConnector:
    source_type = "local_csv"

    def __init__(self, path: str | Path, name: str | None = None) -> None:
        self.path = Path(path)
        self.name = name or self.path.stem
        self.uri = str(self.path)

    def load(self) -> IngestionPayload:
        with self.path.open(encoding="utf-8-sig", newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        return IngestionPayload(
            source_name=self.name,
            source_type=self.source_type,
            uri=self.uri,
            articles=[RawArticle(**_drop_empty_values(row)) for row in rows],
        )


def _drop_empty_values(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if value not in {None, ""}}


def _strip_article_fields(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(row)
    cleaned.pop("id", None)
    cleaned.pop("content_hash", None)
    cleaned.pop("cleaned_text", None)
    cleaned.pop("language", None)
    return cleaned


def _strip_comment_fields(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(row)
    cleaned.pop("id", None)
    cleaned.pop("content_hash", None)
    cleaned.pop("cleaned_text", None)
    cleaned.pop("language", None)
    return cleaned
