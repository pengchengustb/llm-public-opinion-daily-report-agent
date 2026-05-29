# LLM-enhanced Public Opinion Monitoring and Daily Risk Report Generation System

This repository contains the foundation for a master's-level public opinion monitoring system. The final system is designed to ingest multi-source public opinion data, clean and deduplicate documents, persist source-traceable records, run structured LLM-assisted analysis, score public risks, generate Markdown/HTML/PDF daily reports, expose a FastAPI backend, and provide a Streamlit dashboard.

PR #1 establishes the production-ready project foundation. Real scraping and real LLM provider calls are intentionally deferred to later coherent PRs.

## Current Capabilities

- FastAPI backend skeleton with `/health`.
- Streamlit dashboard skeleton that checks backend health.
- Pydantic settings and schema foundation.
- SQLModel database configuration and initial durable entities.
- Logging setup.
- Pytest suite for settings, schemas, database metadata, and API health.
- Docker Compose for running backend and dashboard together.
- GitHub Actions CI for linting, testing, and compilation.
- Documentation for product requirements and architecture.

## Architecture Snapshot

```text
sources -> ingestion -> preprocessing -> database -> analysis -> risk scoring -> reports
                                      |               |             |
                                      v               v             v
                                  FastAPI        Streamlit      evaluation
```

The first PR implements the framework around this architecture, not the full pipeline behavior.

## Requirements

- Python 3.11+
- Docker and Docker Compose, optional but recommended

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

## Run the Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response shape:

```json
{
  "status": "ok",
  "service": "Public Opinion Daily Report Agent",
  "version": "0.1.0",
  "environment": "local"
}
```

## Run the Dashboard

In a separate terminal after starting the backend:

```bash
streamlit run dashboard/Home.py
```

Open <http://localhost:8501>.

## Run with Docker Compose

```bash
docker compose up --build
```

Services:

- Backend: <http://localhost:8000>
- Dashboard: <http://localhost:8501>

Stop services:

```bash
docker compose down
```

Docker Compose uses `.env.example` defaults and stores local SQLite data under `./data`.

## Testing and Quality Checks

```bash
pytest
ruff check .
python -m compileall app tests dashboard
```

## Configuration

Configuration is loaded from environment variables and `.env` via `app/config/settings.py`. `.env.example` documents all non-secret defaults. Do not commit real secrets.

Important variables:

- `DATABASE_URL` — defaults to SQLite for local development.
- `LLM_PROVIDER` — defaults to `mock`; real LLM calls are not implemented yet.
- `LLM_MODEL` — currently a mock model identifier.
- `BACKEND_URL` — dashboard backend target.

## Roadmap

1. Project foundation, config, DB, API, dashboard skeleton, CI, Docker.
2. Ingestion connector abstraction and local/RSS ingestion.
3. Cleaning, normalization, deduplication.
4. LLM abstraction, mock mode, prompt versioning.
5. Sentiment, viewpoint, risk, and evidence extraction.
6. Risk scoring and trend aggregation.
7. Markdown/HTML/PDF report generation.
8. Full Streamlit monitoring dashboard.
9. Daily scheduler and idempotent pipeline runs.
10. Evaluation suite, baselines, metrics, and research documentation.

## Known Limitations in PR #1

- No real scraping or ingestion connectors are implemented.
- No real LLM provider calls are implemented.
- Dashboard pages are placeholders.
- Alembic migrations are not introduced yet; local development creates SQLModel tables on startup.
- Report generation and evaluation are planned but not implemented.
