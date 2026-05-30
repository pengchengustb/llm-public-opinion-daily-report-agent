"""Reproducible daily workflow automation."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session

from app.analysis.structured import StructuredAnalysisService
from app.core.config import Settings, get_settings
from app.db.seed import seed_sample_data
from app.ingestion.local import LocalCSVConnector, LocalJSONConnector
from app.ingestion.rss import RSSConnector
from app.ingestion.service import IngestionService
from app.reporting.service import ReportArtifacts, ReportGenerationService
from app.risk.service import RiskScoringService


class AutomationRunError(RuntimeError):
    """Raised when the daily automation workflow fails."""

    def __init__(self, message: str, result: AutomationRunResult) -> None:
        super().__init__(message)
        self.result = result


@dataclass
class AutomationStepResult:
    name: str
    status: str
    started_at: str
    finished_at: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class AutomationRunResult:
    status: str
    report_date: date
    started_at: str
    finished_at: str | None = None
    analysis_run_id: str | None = None
    report_id: str | None = None
    markdown_path: str | None = None
    html_path: str | None = None
    log_path: str | None = None
    steps: list[AutomationStepResult] = field(default_factory=list)
    replay_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "report_date": self.report_date.isoformat(),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "analysis_run_id": self.analysis_run_id,
            "report_id": self.report_id,
            "markdown_path": self.markdown_path,
            "html_path": self.html_path,
            "log_path": self.log_path,
            "steps": [step.__dict__ for step in self.steps],
            "replay_commands": self.replay_commands,
        }


class DailyAutomationService:
    """Run the local daily monitoring workflow with structured logs."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        log_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.log_dir = log_dir or self.settings.report_output_dir / "automation_logs"

    def run(
        self,
        report_date: date,
        ingest_paths: list[Path] | None = None,
        seed_sample: bool = False,
        analysis_limit: int = 50,
    ) -> AutomationRunResult:
        result = AutomationRunResult(
            status="running",
            report_date=report_date,
            started_at=_utc_timestamp(),
            replay_commands=self._build_replay_commands(report_date, ingest_paths, seed_sample),
        )
        try:
            if seed_sample:
                self._run_step(
                    result,
                    "seed_sample",
                    lambda: seed_sample_data(self.session),
                )

            for path in ingest_paths or []:
                self._run_step(
                    result,
                    f"ingest:{path}",
                    lambda path=path: self._ingest_path(path),
                )

            analysis_run = self._run_step(
                result,
                "analyze_recent_evidence",
                lambda: StructuredAnalysisService(
                    self.session,
                    self.settings,
                ).analyze_recent_evidence(limit=analysis_limit),
            )
            result.analysis_run_id = analysis_run.id

            risks = self._run_step(
                result,
                "score_risks",
                lambda: RiskScoringService(self.session).score_analysis_run(analysis_run.id),
            )

            artifacts = self._run_step(
                result,
                "generate_report",
                lambda: ReportGenerationService(
                    self.session,
                    self.settings,
                ).generate_daily_report(
                    report_date=report_date,
                    analysis_run_id=analysis_run.id,
                ),
            )
            self._record_artifacts(result, artifacts)
            result.steps[-1].detail["risk_scores"] = [
                risk.deterministic_score for risk in risks
            ]
            result.status = "completed"
            return result
        except Exception as exc:
            result.status = "failed"
            raise AutomationRunError("Daily automation workflow failed.", result) from exc
        finally:
            result.finished_at = _utc_timestamp()
            self._write_log(result)

    def _run_step(
        self,
        result: AutomationRunResult,
        name: str,
        action: Callable[[], Any],
    ) -> Any:
        step = AutomationStepResult(name=name, status="running", started_at=_utc_timestamp())
        result.steps.append(step)
        try:
            output = action()
            step.status = "completed"
            step.detail = _summarize_output(output)
            return output
        except Exception as exc:
            step.status = "failed"
            step.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            step.finished_at = _utc_timestamp()

    def _ingest_path(self, path: Path):
        suffix = path.suffix.lower()
        if suffix == ".json":
            connector = LocalJSONConnector(path)
        elif suffix == ".csv":
            connector = LocalCSVConnector(path)
        elif suffix in {".rss", ".xml"}:
            connector = RSSConnector(path)
        else:
            raise ValueError(f"Unsupported ingestion file type: {suffix}")
        return IngestionService(self.session).ingest(connector)

    def _record_artifacts(
        self,
        result: AutomationRunResult,
        artifacts: ReportArtifacts,
    ) -> None:
        result.report_id = artifacts.report.id
        result.markdown_path = str(artifacts.markdown_path)
        result.html_path = str(artifacts.html_path)

    def _write_log(self, result: AutomationRunResult) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = result.started_at.replace(":", "").replace("-", "")
        path = self.log_dir / f"daily_run_{result.report_date.isoformat()}_{timestamp}.json"
        result.log_path = str(path)
        path.write_text(
            json.dumps(_json_safe(result.to_dict()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _build_replay_commands(
        self,
        report_date: date,
        ingest_paths: list[Path] | None,
        seed_sample: bool,
    ) -> list[str]:
        command = ["python -m app run-daily", f"--date {report_date.isoformat()}"]
        if seed_sample:
            command.append("--seed-sample")
        for path in ingest_paths or []:
            command.append(f"--ingest-local {path}")
        return [" ".join(command)]


def _summarize_output(output: Any) -> dict[str, Any]:
    if hasattr(output, "model_dump"):
        return _json_safe(output.model_dump())
    if isinstance(output, dict):
        return _json_safe(output)
    if isinstance(output, list):
        return {"count": len(output)}
    details: dict[str, Any] = {}
    for attr in ("id", "status", "markdown_path", "html_path"):
        if hasattr(output, attr):
            details[attr] = str(getattr(output, attr))
    return details


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_json_safe(item) for item in value]
    return value


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()
