"""RSS connector for feed-style article ingestion."""

from __future__ import annotations

from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

from app.ingestion.contracts import IngestionPayload, RawArticle


class RSSConnector:
    source_type = "rss"

    def __init__(
        self,
        uri: str | Path,
        name: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.uri = str(uri)
        self.name = name or Path(str(uri)).stem or "rss-feed"
        self.timeout_seconds = timeout_seconds

    def load(self) -> IngestionPayload:
        xml_text = self._read_xml()
        root = ElementTree.fromstring(xml_text)
        channel = root.find("channel")
        source_name = _text(channel, "title") if channel is not None else self.name
        items = channel.findall("item") if channel is not None else root.findall(".//item")

        articles = []
        for item in items:
            title = _text(item, "title") or "Untitled RSS item"
            description = _text(item, "description") or title
            articles.append(
                RawArticle(
                    external_id=_text(item, "guid") or _text(item, "link") or title,
                    title=title,
                    raw_text=description,
                    url=_text(item, "link"),
                    author=_text(item, "author"),
                    published_at=_parse_rss_datetime(_text(item, "pubDate")),
                )
            )

        return IngestionPayload(
            source_name=source_name or self.name,
            source_type=self.source_type,
            uri=self.uri,
            articles=articles,
        )

    def _read_xml(self) -> str:
        if self.uri.startswith(("http://", "https://")):
            with urlopen(self.uri, timeout=self.timeout_seconds) as response:
                return response.read().decode("utf-8")
        return Path(self.uri).read_text(encoding="utf-8")


def _text(element: ElementTree.Element | None, child_name: str) -> str | None:
    if element is None:
        return None
    child = element.find(child_name)
    if child is None or child.text is None:
        return None
    return child.text.strip() or None


def _parse_rss_datetime(value: str | None):
    if value is None:
        return None
    return parsedate_to_datetime(value)
