# Product Requirements Document

## Product Vision

Build a complete, evaluable, and reproducible LLM-enhanced system for monitoring public opinion and generating daily risk reports with evidence traceability.

## Goals

- Collect public opinion documents from multiple source types.
- Clean, normalize, deduplicate, and persist source records.
- Run structured sentiment, viewpoint, and risk analysis.
- Preserve evidence traceability from every conclusion back to source documents.
- Generate daily Markdown, HTML, and PDF reports.
- Provide a Streamlit dashboard for exploration and monitoring.
- Support scheduled daily execution.
- Include evaluation datasets, baselines, metrics, and error analysis.
- Provide Docker Compose and CI for reproducible development.

## Non-goals for PR #1

- Real scraping.
- Real LLM provider calls.
- Production authentication.
- Full report generation.
- Full evaluation suite.

## Users

- Graduate student/researcher building a portfolio-quality applied AI system.
- Analyst reviewing public opinion trends and risk signals.
- Reviewer evaluating evidence traceability and methodology.

## Functional Requirements

1. Configure the system without hard-coded secrets.
2. Start a FastAPI backend locally and in Docker.
3. Start a Streamlit dashboard locally and in Docker.
4. Persist future source and analysis records through SQLModel entities.
5. Validate future structured model outputs with Pydantic schemas.
6. Provide tests and CI from the first PR.
7. Document the target architecture and staged roadmap.

## Quality Requirements

- Python 3.11+.
- Typed Pydantic settings and schemas.
- SQLModel-based persistence foundation.
- Deterministic mock mode for future AI tests.
- Modular code layout suitable for staged implementation.
- Clear documentation and commands for new contributors.
