"""Developer-facing command entrypoints for reproducible workflows."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import uvicorn

from app.core.config import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opinion-monitor",
        description="Run public opinion monitoring development commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    api_parser = subparsers.add_parser("api", help="Start the FastAPI backend.")
    api_parser.add_argument("--reload", action="store_true", help="Enable development reload.")

    subparsers.add_parser("seed-sample", help="Create tables and load deterministic sample data.")

    ingest_parser = subparsers.add_parser(
        "ingest-local",
        help="Ingest a local JSON, CSV, or RSS/XML file.",
    )
    ingest_parser.add_argument("path", help="Path to a local .json, .csv, .rss, or .xml file.")

    analyze_parser = subparsers.add_parser(
        "analyze-mock",
        help="Run deterministic structured analysis over persisted evidence.",
    )
    analyze_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum articles/comments to read.",
    )

    score_parser = subparsers.add_parser(
        "score-risks",
        help="Run deterministic risk scoring for an analysis run.",
    )
    score_parser.add_argument("--analysis-run-id", default=None, help="Analysis run to score.")

    report_parser = subparsers.add_parser(
        "generate-report",
        help="Generate Markdown and HTML daily reports from persisted analysis outputs.",
    )
    report_parser.add_argument("--analysis-run-id", default=None, help="Analysis run to report.")
    report_parser.add_argument(
        "--date",
        dest="report_date",
        default=None,
        help="Report date in YYYY-MM-DD format. Defaults to today.",
    )
    report_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for generated report artifacts. Defaults to REPORT_OUTPUT_DIR.",
    )

    daily_parser = subparsers.add_parser(
        "run-daily",
        help="Run the reproducible daily seed/ingest/analyze/score/report workflow.",
    )
    daily_parser.add_argument(
        "--date",
        dest="report_date",
        default=None,
        help="Report date in YYYY-MM-DD format. Defaults to today.",
    )
    daily_parser.add_argument(
        "--ingest-local",
        dest="ingest_paths",
        action="append",
        default=[],
        help="Local JSON, CSV, RSS, or XML file to ingest before analysis. Repeatable.",
    )
    daily_parser.add_argument(
        "--seed-sample",
        action="store_true",
        help="Load deterministic sample data before analysis.",
    )
    daily_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum articles/comments to analyze.",
    )

    eval_parser = subparsers.add_parser(
        "evaluate-mock",
        help="Run deterministic mock evaluation and write evaluation artifacts.",
    )
    eval_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for evaluation artifacts. Defaults to REPORT_OUTPUT_DIR/evaluation.",
    )

    validate_parser = subparsers.add_parser(
        "validate-demo",
        help="Run the final deterministic demo validation workflow.",
    )
    validate_parser.add_argument(
        "--date",
        dest="report_date",
        default=None,
        help="Report date in YYYY-MM-DD format. Defaults to today.",
    )
    validate_parser.add_argument(
        "--skip-seed-sample",
        action="store_true",
        help="Do not load deterministic sample data before validation.",
    )
    validate_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for final validation reports. Defaults to REPORT_OUTPUT_DIR/validation.",
    )

    subparsers.add_parser("doctor", help="Print resolved runtime configuration.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()

    if args.command == "api":
        uvicorn.run(
            "app.main:create_app",
            factory=True,
            host=settings.api_host,
            port=settings.api_port,
            reload=args.reload,
        )
        return

    if args.command == "doctor":
        print(settings.model_dump_json(indent=2, exclude={"openai_api_key"}))
        return

    if args.command == "seed-sample":
        from sqlmodel import Session

        from app.db.seed import seed_sample_data
        from app.db.session import create_database_engine, create_db_and_tables

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        try:
            with Session(engine) as session:
                result = seed_sample_data(session)
        finally:
            engine.dispose()
        print(f"Seed sample complete: {result}")
        return

    if args.command == "ingest-local":
        from sqlmodel import Session

        from app.db.session import create_database_engine, create_db_and_tables
        from app.ingestion.local import LocalCSVConnector, LocalJSONConnector
        from app.ingestion.rss import RSSConnector
        from app.ingestion.service import IngestionService

        path = Path(args.path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            connector = LocalJSONConnector(path)
        elif suffix == ".csv":
            connector = LocalCSVConnector(path)
        elif suffix in {".rss", ".xml"}:
            connector = RSSConnector(path)
        else:
            raise SystemExit(f"Unsupported ingestion file type: {suffix}")

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        try:
            with Session(engine) as session:
                result = IngestionService(session).ingest(connector)
        finally:
            engine.dispose()
        print(result.model_dump_json(indent=2))
        return

    if args.command == "analyze-mock":
        from sqlmodel import Session

        from app.analysis.structured import StructuredAnalysisService
        from app.db.session import create_database_engine, create_db_and_tables

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        try:
            with Session(engine) as session:
                analysis_run = StructuredAnalysisService(session, settings).analyze_recent_evidence(
                    limit=args.limit,
                )
        finally:
            engine.dispose()
        print(
            f"Structured mock analysis complete: run_id={analysis_run.id} "
            f"status={analysis_run.status}"
        )
        return

    if args.command == "score-risks":
        from sqlmodel import Session

        from app.db.session import create_database_engine, create_db_and_tables
        from app.risk.service import RiskScoringService

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        try:
            with Session(engine) as session:
                service = RiskScoringService(session)
                if args.analysis_run_id:
                    risks = service.score_analysis_run(args.analysis_run_id)
                else:
                    risks = service.score_latest_analysis_run()
        finally:
            engine.dispose()
        print(
            "Deterministic risk scoring complete: "
            f"risks={len(risks)} scores={[risk.deterministic_score for risk in risks]}"
        )
        return

    if args.command == "generate-report":
        from sqlmodel import Session

        from app.db.session import create_database_engine, create_db_and_tables
        from app.reporting.service import ReportGenerationService

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        report_date = date.fromisoformat(args.report_date) if args.report_date else None
        output_dir = Path(args.output_dir) if args.output_dir else None
        try:
            with Session(engine) as session:
                artifacts = ReportGenerationService(
                    session,
                    settings,
                    output_dir=output_dir,
                ).generate_daily_report(
                    report_date=report_date,
                    analysis_run_id=args.analysis_run_id,
                )
        finally:
            engine.dispose()
        print(
            "Daily report generated: "
            f"report_id={artifacts.report.id} markdown={artifacts.markdown_path} "
            f"html={artifacts.html_path}"
        )
        return

    if args.command == "run-daily":
        from sqlmodel import Session

        from app.automation.daily import AutomationRunError, DailyAutomationService
        from app.db.session import create_database_engine, create_db_and_tables

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        report_date = date.fromisoformat(args.report_date) if args.report_date else date.today()
        ingest_paths = [Path(path) for path in args.ingest_paths]
        try:
            with Session(engine) as session:
                result = DailyAutomationService(session, settings).run(
                    report_date=report_date,
                    ingest_paths=ingest_paths,
                    seed_sample=args.seed_sample,
                    analysis_limit=args.limit,
                )
        except AutomationRunError as exc:
            result = exc.result
            print(
                "Daily workflow failed: "
                f"steps={[(step.name, step.status) for step in result.steps]} "
                f"log={result.log_path}"
            )
            raise SystemExit(1) from exc
        finally:
            engine.dispose()
        print(
            "Daily workflow complete: "
            f"analysis_run_id={result.analysis_run_id} report_id={result.report_id} "
            f"markdown={result.markdown_path} html={result.html_path} log={result.log_path}"
        )
        return

    if args.command == "evaluate-mock":
        from sqlmodel import Session

        from app.db.session import create_database_engine, create_db_and_tables
        from app.evaluation.service import EvaluationService

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        output_dir = Path(args.output_dir) if args.output_dir else None
        try:
            with Session(engine) as session:
                artifacts = EvaluationService(
                    session,
                    settings,
                    output_dir=output_dir,
                ).run_mock_evaluation()
        finally:
            engine.dispose()
        print(
            "Mock evaluation complete: "
            f"evaluation_run_id={artifacts.evaluation_run.id} "
            f"report={artifacts.report_path} metrics={artifacts.metrics_path} "
            f"metrics={artifacts.metrics}"
        )
        return

    if args.command == "validate-demo":
        from sqlmodel import Session

        from app.db.session import create_database_engine, create_db_and_tables
        from app.validation.demo import DemoValidationService

        create_db_and_tables(settings)
        engine = create_database_engine(settings)
        report_date = date.fromisoformat(args.report_date) if args.report_date else date.today()
        output_dir = Path(args.output_dir) if args.output_dir else None
        try:
            with Session(engine) as session:
                result = DemoValidationService(
                    session,
                    settings,
                    output_dir=output_dir,
                ).run(
                    report_date=report_date,
                    seed_sample=not args.skip_seed_sample,
                )
        finally:
            engine.dispose()
        print(
            "Demo validation complete: "
            f"status={result.status} report={result.validation_report_path} "
            f"checks={[(check.name, check.status) for check in result.checks]}"
        )
        if result.status != "passed":
            raise SystemExit(1)
