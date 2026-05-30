"""Built-in mock-mode evaluation samples."""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.contracts import EvidenceItem


@dataclass(frozen=True)
class EvaluationCase:
    evidence_id: str
    entity_type: str
    text: str
    expected_sentiment: str
    title: str | None = None
    engagement_score: int = 0

    def to_evidence_item(self) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=self.evidence_id,
            entity_type=self.entity_type,
            text=self.text,
            title=self.title,
            engagement_score=self.engagement_score,
        )


DEFAULT_MOCK_CASES = [
    EvaluationCase(
        evidence_id="eval-positive-1",
        entity_type="article",
        title="Service response improved",
        text="Residents say the service is stable and support improved after the update.",
        expected_sentiment="positive",
        engagement_score=12,
    ),
    EvaluationCase(
        evidence_id="eval-negative-1",
        entity_type="comment",
        text="Users worry about delay, complaint handling, and public risk.",
        expected_sentiment="negative",
        engagement_score=24,
    ),
    EvaluationCase(
        evidence_id="eval-neutral-1",
        entity_type="article",
        title="Routine briefing released",
        text="The office published a routine briefing with schedule details.",
        expected_sentiment="neutral",
        engagement_score=3,
    ),
]
