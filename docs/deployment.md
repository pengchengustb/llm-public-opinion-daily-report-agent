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

## Docker Compose

Validate configuration:

```bash
docker compose config
```

Start services:

```bash
docker compose up --build
```

## Environment

Use `.env.example` as the template for local `.env`. Keep `LLM_MOCK_MODE=true` until the real OpenAI client is implemented in a later PR.

## CI

GitHub Actions installs the package with development dependencies, runs Ruff, runs pytest, and compiles Python files on Python 3.11 and 3.12.

