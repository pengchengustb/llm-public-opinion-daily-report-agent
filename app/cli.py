"""Developer-facing command entrypoints for reproducible workflows."""

from __future__ import annotations

import argparse

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
