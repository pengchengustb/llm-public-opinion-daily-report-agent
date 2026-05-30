# Agent Guide

This project is a staged master's-level public opinion monitoring system. Preserve the architecture even when implementing small PRs.

## Development Rules

- Keep PRs small but meaningful.
- Update tests and docs whenever behavior changes.
- Do not hard-code secrets or credentials.
- Do not import provider SDKs outside `app/llm`.
- Keep generated runtime data out of Git.
- Prefer typed schemas, explicit evidence IDs, and deterministic mock behavior in tests.

## Project Boundaries

- Backend API code belongs in `app/api`.
- Runtime settings and logging belong in `app/core`.
- Persistence setup and SQLModel models belong in `app/db`.
- Future ingestion connectors belong in `app/ingestion`.
- Future cleaning, dedupe, and quality checks belong in `app/preprocessing`.
- Future OpenAI calls must go through `app/llm`.
- Future report assembly and exporters belong in `app/reporting`.
- Evaluation datasets, metrics, and report generation belong in `app/evaluation`.

## PR #1 Expectations

PR #1 is a foundation slice. It should prove the project can start, test, and support the full roadmap. It must not implement real scraping, real LLM calls, or PDF export.

## Verification

Run when dependencies are installed:

```bash
ruff check .
pytest
python -m compileall app tests dashboard
```

