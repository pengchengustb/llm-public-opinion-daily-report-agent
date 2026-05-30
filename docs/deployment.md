# Deployment

## Local Development

Install dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run backend:

```bash
python -m app api --reload
```

Run dashboard:

```bash
streamlit run dashboard/app.py
```

Run the deterministic local daily workflow:

```bash
python -m app run-daily --seed-sample
```

Run the final deterministic validation workflow:

```bash
python -m app validate-demo --date 2026-05-30
```

Run with local ingestion inputs:

```bash
python -m app run-daily --ingest-local data/samples/local_articles.csv --ingest-local data/samples/rss_sample.xml
```

The command writes generated reports under `REPORT_OUTPUT_DIR` and structured automation logs under `REPORT_OUTPUT_DIR/automation_logs`. In production, schedule this command with cron, Windows Task Scheduler, GitHub Actions, or a container scheduler.

## Docker Compose

Validate configuration:

```bash
docker compose config
```

Start services:

```bash
docker compose up --build
```

Run the daily workflow in the backend container:

```bash
docker compose run --rm backend python -m app run-daily --seed-sample
```

## Environment

Use `.env.example` as the template for local `.env`. Keep `LLM_MOCK_MODE=true` until the real OpenAI client is implemented in a later PR.

## CI

GitHub Actions installs the package with development dependencies, runs Ruff, runs pytest, and compiles Python files on Python 3.11 and 3.12.
