# Product Requirements Document

## Product Vision

The system monitors public opinion from news articles and user comments, analyzes sentiment and risk with evidence-traceable LLM workflows, and generates Chinese daily risk reports for decision makers.

## Users

- Researcher or graduate student demonstrating a complete applied AI system.
- Analyst reviewing public opinion trends and risk signals.
- Developer extending ingestion, analysis, reporting, and evaluation modules.

## Goals

- Ingest local files and RSS sources through extensible connectors.
- Validate, clean, deduplicate, and summarize data quality.
- Persist articles, comments, analysis runs, LLM outputs, risk insights, and reports.
- Use structured LLM outputs with evidence IDs and deterministic mock mode.
- Combine deterministic risk metrics with LLM explanations.
- Generate daily Markdown, HTML, and later PDF reports.
- Provide a Streamlit dashboard for monitoring, evidence review, and downloads.
- Include evaluation workflows for sentiment, risk, viewpoints, and report quality.

## Non-goals For PR #1

- No real LLM provider calls.
- No real scraping or RSS ingestion.
- No PDF generation.
- No production dashboard charts.

## Success Criteria

- Backend starts and responds on `/health`.
- Dashboard starts and can show backend health.
- Tests pass in CI.
- Docker Compose can run backend and dashboard.
- Documentation explains architecture, setup, roadmap, and limitations.

