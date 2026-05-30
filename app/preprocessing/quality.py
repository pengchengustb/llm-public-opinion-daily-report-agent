"""Data quality issue models and summaries."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class DataQualityIssue:
    entity_type: str
    issue_type: str
    severity: str
    message: str
    entity_id: str | None = None


@dataclass(frozen=True)
class DataQualitySummary:
    issue_count: int
    by_severity: dict[str, int]
    by_type: dict[str, int]


def summarize_quality_issues(issues: list[DataQualityIssue]) -> DataQualitySummary:
    return DataQualitySummary(
        issue_count=len(issues),
        by_severity=dict(Counter(issue.severity for issue in issues)),
        by_type=dict(Counter(issue.issue_type for issue in issues)),
    )
