"""Portfolio-ready final validation workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from sqlmodel import Session

from app.automation.daily import DailyAutomationService
from app.core.config import Settings, get_settings
from app.evaluation.service import EvaluationService


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    status: str
    detail: str


@dataclass
class DemoValidationResult:
    status: str
    report_date: date
    analysis_run_id: str | None
    report_id: str | None
    evaluation_run_id: str | None
    validation_report_path: str | None
    checks: list[ValidationCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "report_date": self.report_date.isoformat(),
            "analysis_run_id": self.analysis_run_id,
            "report_id": self.report_id,
            "evaluation_run_id": self.evaluation_run_id,
            "validation_report_path": self.validation_report_path,
            "checks": [check.__dict__ for check in self.checks],
        }


class DemoValidationService:
    """Run the full deterministic demo and write a final validation report."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.output_dir = output_dir or self.settings.report_output_dir / "validation"

    def run(self, report_date: date, seed_sample: bool = True) -> DemoValidationResult:
        daily_result = DailyAutomationService(self.session, self.settings).run(
            report_date=report_date,
            seed_sample=seed_sample,
        )
        evaluation_artifacts = EvaluationService(self.session, self.settings).run_mock_evaluation()

        checks = [
            _file_exists_check("markdown_report_exists", daily_result.markdown_path),
            _file_exists_check("html_report_exists", daily_result.html_path),
            _file_exists_check("automation_log_exists", daily_result.log_path),
            _file_exists_check("evaluation_report_exists", str(evaluation_artifacts.report_path)),
            _metric_threshold_check(
                "sentiment_accuracy_threshold",
                evaluation_artifacts.metrics["sentiment_accuracy"],
                0.8,
            ),
            _metric_threshold_check(
                "evidence_coverage_threshold",
                evaluation_artifacts.metrics["evidence_citation_coverage"],
                1.0,
            ),
            _metric_threshold_check(
                "report_completeness_threshold",
                evaluation_artifacts.metrics["report_completeness"],
                1.0,
            ),
        ]
        status = "passed" if all(check.status == "passed" for check in checks) else "failed"
        result = DemoValidationResult(
            status=status,
            report_date=report_date,
            analysis_run_id=daily_result.analysis_run_id,
            report_id=daily_result.report_id,
            evaluation_run_id=evaluation_artifacts.evaluation_run.id,
            validation_report_path=None,
            checks=checks,
        )
        result.validation_report_path = str(self._write_report(result))
        return result

    def _write_report(self, result: DemoValidationResult) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"final_validation_{result.report_date.isoformat()}.md"
        rows = "\n".join(
            f"| {check.name} | {check.status} | {check.detail} |" for check in result.checks
        )
        path.write_text(
            f"""# Final Validation Report

Status: **{result.status}**

Report date: `{result.report_date.isoformat()}`

- Analysis run: `{result.analysis_run_id}`
- Daily report: `{result.report_id}`
- Evaluation run: `{result.evaluation_run_id}`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
{rows}
""",
            encoding="utf-8",
        )
        return path


def _file_exists_check(name: str, path: str | None) -> ValidationCheck:
    if path and Path(path).exists():
        return ValidationCheck(name=name, status="passed", detail=path)
    return ValidationCheck(name=name, status="failed", detail=path or "missing path")


def _metric_threshold_check(name: str, value: float, threshold: float) -> ValidationCheck:
    status = "passed" if value >= threshold else "failed"
    return ValidationCheck(
        name=name,
        status=status,
        detail=f"value={value:.4f}, threshold={threshold:.4f}",
    )
