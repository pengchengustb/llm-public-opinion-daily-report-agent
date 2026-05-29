# LLM-enhanced Public Opinion Monitoring and Daily Risk Report Generation System

This repository is the foundation for a master's-level system that ingests news articles and user comments, analyzes public opinion with LLM-assisted structured workflows, detects sentiment and risks, and generates daily risk reports. PR #1 intentionally creates the extensible architecture without implementing real LLM calls, scraping, or PDF export yet.

User-facing dashboard and generated report text are planned primarily in Chinese. Code, schemas, and repository documentation use English for maintainability.

## Current Scope

Implemented in the foundation slice:

- FastAPI backend skeleton with `/health`.
- Streamlit dashboard skeleton with backend health status and planned pages.
- Typed configuration and logging setup.
- SQLite-first database foundation with PostgreSQL-compatible configuration.
- Core schemas for articles, comments, analysis runs, sentiment, viewpoints, risks, and daily reports.
- Isolated `app/llm` boundary with deterministic mock client placeholder.
- pytest, Ruff, Docker Compose, GitHub Actions CI, and project documentation.

Implemented in the persistence slice:

- Complete SQLModel table coverage for ingestion batches, data quality records, topic summaries, recommendations, reports, and evaluation metrics.
- Lightweight repository helpers for early service code and tests.
- Deterministic Chinese sample data under `data/samples/`.
- CLI sample seeding through `python -m app seed-sample`.

Implemented in the ingestion/preprocessing slice:

- Local JSON and CSV connectors.
- RSS/XML connector for feed-style article ingestion.
- Text cleaning, lightweight language detection, content hashing, and dedupe.
- Data quality issue persistence and summary counts.
- CLI ingestion through `python -m app ingest-local <path>`.

Not implemented yet:

- Real OpenAI calls.
- Real scraping or RSS ingestion.
- Full analysis, scoring, report generation, or PDF export.
- Production dashboard charts and downloads.

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

Run the backend:

```bash
python -m app api --reload
```

Open the backend health check:

```bash
curl http://localhost:8000/health
```

Run the dashboard in another terminal:

```bash
streamlit run dashboard/app.py
```

Then open `http://localhost:8501`.

Create local SQLite tables and load deterministic sample data:

```bash
python -m app seed-sample
```

Ingest local sample files:

```bash
python -m app ingest-local data/samples/local_articles.csv
python -m app ingest-local data/samples/rss_sample.xml
python -m app ingest-local data/samples/opinion_sample.json
```

## Testing And Quality

```bash
pytest
ruff check .
python -m compileall app tests dashboard
```

Some tests import optional runtime dependencies and are skipped automatically if the local environment has not installed the project dependencies. In CI, dependencies are installed with `python -m pip install -e ".[dev]"`, so backend and schema smoke tests run normally.

## Docker Compose

Validate the Compose file:

```bash
docker compose config
```

Start backend and dashboard:

```bash
docker compose up --build
```

Services:

- Backend: `http://localhost:8000`
- Dashboard: `http://localhost:8501`

Runtime database files are stored under `data/generated/`, and generated reports will be stored under `reports/`. Both are gitignored.

## Configuration

Copy `.env.example` to `.env` for local development. Important settings:

- `DATABASE_URL`: defaults to SQLite at `data/generated/opinion_monitor.db`.
- `LLM_MOCK_MODE`: defaults to `true`; real LLM calls are intentionally deferred.
- `OPENAI_API_KEY`: documented but unused until the real LLM client PR.
- `REPORT_LANGUAGE`: defaults to `zh-CN`.

Never commit `.env` or secrets.

## Architecture Direction

The repository is organized around stable boundaries:

- `app/api`: FastAPI routers.
- `app/core`: config, logging, shared runtime helpers.
- `app/db`: SQLModel engine/session and persistence models.
- `app/ingestion`: local/RSS/source connectors in later PRs.
- `app/preprocessing`: validation, cleaning, dedupe, quality summaries.
- `app/llm`: the only allowed boundary for LLM provider calls.
- `app/analysis`: sentiment, viewpoint, topic, recommendation services.
- `app/risk`: deterministic scoring and trend analysis.
- `app/reporting`: Markdown/HTML/PDF report generation.
- `app/evaluation`: benchmarks and evaluation reports.

See `docs/architecture.md` and `docs/roadmap.md` for the complete plan.
