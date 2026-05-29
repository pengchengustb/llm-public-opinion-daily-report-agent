# AGENTS.md

## Project Goal

This repository implements a master's-level LLM-enhanced Public Opinion Monitoring and Daily Risk Report Generation System.

The project is not a toy MVP. It should be a complete, usable, well-documented, and evaluable system.

## Core Requirements

The system must support:
- multi-source data ingestion
- data cleaning and deduplication
- persistent storage
- LLM-based structured analysis
- sentiment analysis
- viewpoint extraction
- risk classification and scoring
- evidence traceability
- Markdown, HTML, and PDF report generation
- dashboard visualization
- scheduled daily execution
- evaluation suite
- reproducible deployment

## Engineering Standards

- Use Python 3.11+.
- Use FastAPI for backend APIs.
- Use Streamlit for the dashboard unless otherwise specified.
- Use Pydantic for schemas.
- Use SQLModel or SQLAlchemy for database models.
- Use pytest for tests.
- Use Docker Compose for reproducible local deployment.
- Keep OpenAI API calls isolated in a dedicated `app/llm` module.
- Never hard-code secrets.
- Use `.env.example` for configuration documentation.
- Prefer modular packages over one-off scripts.
- Keep deterministic mock paths for tests.

## Repository Layout Standards

- `app/` contains backend, pipeline, schemas, persistence, and analysis modules.
- `dashboard/` contains Streamlit pages and components.
- `docs/` contains architecture, PRD, methodology, deployment, and evaluation documentation.
- `tests/` contains pytest unit and integration tests.
- `data/` and `reports/` may contain `.gitkeep` placeholders, but generated runtime artifacts should not be committed unless explicitly documented as fixtures.

## AI Analysis Standards

- Prefer structured JSON outputs.
- Validate all LLM outputs with Pydantic.
- Every sentiment, viewpoint, and risk conclusion must include source IDs.
- Keep prompt templates versioned.
- Include mock mode for tests.
- Log model name, prompt version, token usage, and analysis run ID.
- Do not implement provider-specific LLM calls outside `app/llm`.

## Research Standards

The project should include:
- research questions
- methodology documentation
- baseline comparison
- evaluation dataset
- evaluation metrics
- error analysis
- limitations section

## Pull Request Standards

Each PR must:
- implement one coherent module or foundation slice
- include or update tests
- update README/docs if behavior changes
- pass pytest
- summarize changed files
- include commands run
- include known limitations

## Review Guidelines

When reviewing, check:
- missing tests
- broken CLI/API behavior
- unvalidated LLM outputs
- lack of source traceability
- hard-coded secrets
- over-engineering
- unclear documentation
