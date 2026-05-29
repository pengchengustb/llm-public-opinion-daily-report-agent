# Roadmap

## PR #1: Project Foundation

Create packaging, FastAPI skeleton, Streamlit skeleton, database config, initial schemas, configuration/logging, pytest, Docker Compose, CI, README, documentation, and agent guidance.

Status: implemented on `codex/project-foundation`.

## PR #2: Persistence And Domain Models

Complete SQLModel schema, repository/session helpers, seed samples, and persistence tests.

Status: implemented on `codex/persistence-domain-models`.

## PR #3: Ingestion And Preprocessing

Add local JSON/CSV ingestion, RSS ingestion, connector interface, validation, cleaning, dedupe, optional language detection, and data quality summaries.

Status: implemented on `codex/ingestion-preprocessing`.

## PR #4: LLM Client And Structured Analysis

Add OpenAI client abstraction, mock client fixtures, prompt templates, structured sentiment/viewpoint/topic/risk/recommendation services, and mock-mode tests.

Status: implemented on `codex/llm-structured-analysis`.

## PR #5: Risk Scoring And Trend Analysis

Implement deterministic risk scoring, topic growth, high-engagement negative comment handling, sensitive-topic scoring, uncertainty scoring, and explanations.

## PR #6: Report Generation

Add daily report assembly, Jinja2 templates, Markdown/HTML export, PDF export selection, archive management, and traceability checks.

## PR #7: Dashboard

Build date selector, sentiment charts, topic ranking, risk ranking, representative evidence, run status, and report download views.

## PR #8: Automation

Add daily scheduled command, structured logs, failure handling, reproducible commands, and Docker documentation.

## PR #9: Evaluation Suite

Implement benchmark runners, metric calculations, sample gold datasets, `evaluation_report.md`, and CI-friendly mock evaluation.

## PR #10: Hardening And Portfolio Polish

Improve docs, examples, screenshots, error handling, deployment notes, and final validation checklist.
