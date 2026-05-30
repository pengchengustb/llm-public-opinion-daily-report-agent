"""Mock-mode evaluation runner and report writer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db.models import EvaluationMetric, EvaluationRun
from app.evaluation.benchmarks import DEFAULT_MOCK_CASES, EvaluationCase
from app.evaluation.metrics import accuracy, evidence_coverage, macro_f1
from app.llm.client import build_llm_client
from app.llm.contracts import AnalysisInput, StructuredAnalysisOutput


@dataclass(frozen=True)
class EvaluationArtifacts:
    evaluation_run: EvaluationRun
    metrics: dict[str, float]
    report_path: Path
    metrics_path: Path


class EvaluationService:
    """Run deterministic benchmarks and persist evaluation metrics."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.output_dir = output_dir or self.settings.report_output_dir / "evaluation"

    def run_mock_evaluation(
        self,
        cases: list[EvaluationCase] | None = None,
    ) -> EvaluationArtifacts:
        benchmark_cases = cases or DEFAULT_MOCK_CASES
        evaluation_run = EvaluationRun(
            benchmark_name="mock_public_opinion_eval_v0.1",
            status="running",
            provider="mock",
            model_name=self.settings.llm_model,
            mock_mode=True,
            run_metadata={"case_count": len(benchmark_cases)},
        )
        self.session.add(evaluation_run)
        self.session.commit()
        self.session.refresh(evaluation_run)

        try:
            output = build_llm_client(Settings(llm_mock_mode=True)).analyze(
                AnalysisInput(
                    evidence_items=[case.to_evidence_item() for case in benchmark_cases],
                    report_language=self.settings.report_language,
                )
            )
            metrics = self._compute_metrics(benchmark_cases, output)
            report_path, metrics_path = self._write_artifacts(
                evaluation_run.id,
                benchmark_cases,
                output,
                metrics,
            )
            for name, value in metrics.items():
                self.session.add(
                    EvaluationMetric(
                        evaluation_run_id=evaluation_run.id,
                        metric_name=name,
                        metric_value=value,
                        metric_metadata={"benchmark": evaluation_run.benchmark_name},
                    )
                )
            evaluation_run.status = "completed"
            evaluation_run.finished_at = datetime.now(UTC)
            evaluation_run.artifact_path = str(report_path)
            evaluation_run.run_metadata = {
                **evaluation_run.run_metadata,
                "metrics_path": str(metrics_path),
            }
            self.session.add(evaluation_run)
            self.session.commit()
            self.session.refresh(evaluation_run)
            return EvaluationArtifacts(
                evaluation_run=evaluation_run,
                metrics=metrics,
                report_path=report_path,
                metrics_path=metrics_path,
            )
        except Exception:
            evaluation_run.status = "failed"
            evaluation_run.finished_at = datetime.now(UTC)
            self.session.add(evaluation_run)
            self.session.commit()
            raise

    def _compute_metrics(
        self,
        cases: list[EvaluationCase],
        output: StructuredAnalysisOutput,
    ) -> dict[str, float]:
        expected_by_id = {case.evidence_id: case.expected_sentiment for case in cases}
        predicted_by_id = {
            sentiment.entity_id: sentiment.label for sentiment in output.sentiments
        }
        expected = [expected_by_id[case.evidence_id] for case in cases]
        predicted = [predicted_by_id.get(case.evidence_id, "missing") for case in cases]
        known_ids = {case.evidence_id for case in cases}
        referenced_ids = _collect_evidence_ids(output)
        expected_risk_severity = "medium" if "negative" in expected else "low"
        predicted_risk_severity = output.risks[0].severity if output.risks else "missing"

        report_sections = [
            bool(output.daily_report.executive_summary),
            bool(output.daily_report.key_risks),
            bool(output.daily_report.evidence_highlights),
            bool(output.daily_report.recommended_actions),
        ]
        return {
            "sentiment_accuracy": accuracy(expected, predicted),
            "sentiment_macro_f1": macro_f1(expected, predicted),
            "risk_severity_agreement": 1.0
            if expected_risk_severity == predicted_risk_severity
            else 0.0,
            "evidence_citation_coverage": evidence_coverage(referenced_ids, known_ids),
            "report_completeness": round(sum(report_sections) / len(report_sections), 4),
        }

    def _write_artifacts(
        self,
        evaluation_run_id: str,
        cases: list[EvaluationCase],
        output: StructuredAnalysisOutput,
        metrics: dict[str, float],
    ) -> tuple[Path, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = self.output_dir / f"{evaluation_run_id}_metrics.json"
        report_path = self.output_dir / "evaluation_report.md"
        payload: dict[str, Any] = {
            "evaluation_run_id": evaluation_run_id,
            "benchmark_name": "mock_public_opinion_eval_v0.1",
            "metrics": metrics,
            "cases": [case.__dict__ for case in cases],
            "predictions": [sentiment.model_dump() for sentiment in output.sentiments],
        }
        metrics_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report_path.write_text(
            _render_report(evaluation_run_id, metrics, cases, output, metrics_path),
            encoding="utf-8",
        )
        return report_path, metrics_path


def _collect_evidence_ids(output: StructuredAnalysisOutput) -> set[str]:
    evidence_ids: set[str] = set()
    for group in (
        output.sentiments,
        output.viewpoints,
        output.topics,
        output.risks,
        output.recommendations,
    ):
        for item in group:
            evidence_ids.update(item.evidence_ids)
    evidence_ids.update(output.daily_report.evidence_highlights)
    return evidence_ids


def _render_report(
    evaluation_run_id: str,
    metrics: dict[str, float],
    cases: list[EvaluationCase],
    output: StructuredAnalysisOutput,
    metrics_path: Path,
) -> str:
    metric_lines = "\n".join(
        f"| {name} | {value:.4f} |" for name, value in sorted(metrics.items())
    )
    case_lines = "\n".join(
        f"| {case.evidence_id} | {case.expected_sentiment} | "
        f"{_prediction_for(case.evidence_id, output)} |"
        for case in cases
    )
    return f"""# Evaluation Report

Evaluation run: `{evaluation_run_id}`

Metrics artifact: `{metrics_path}`

## Metrics

| Metric | Value |
| --- | ---: |
{metric_lines}

## Sentiment Cases

| Evidence ID | Expected | Predicted |
| --- | --- | --- |
{case_lines}

## Report Quality Checks

- Executive summary present: {bool(output.daily_report.executive_summary)}
- Key risks present: {bool(output.daily_report.key_risks)}
- Evidence highlights present: {bool(output.daily_report.evidence_highlights)}
- Recommended actions present: {bool(output.daily_report.recommended_actions)}
"""


def _prediction_for(evidence_id: str, output: StructuredAnalysisOutput) -> str:
    for sentiment in output.sentiments:
        if sentiment.entity_id == evidence_id:
            return sentiment.label
    return "missing"
