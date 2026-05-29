"""Data ingestion package for local files, RSS, and future connectors."""

from app.ingestion.contracts import IngestionPayload, IngestionSummary, RawArticle, RawComment

__all__ = ["IngestionPayload", "IngestionSummary", "RawArticle", "RawComment"]
