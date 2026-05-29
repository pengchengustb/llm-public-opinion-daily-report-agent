# Implementation Roadmap

## PR 1: Foundation

Backend skeleton, dashboard skeleton, database models, settings, logging, tests, Docker Compose, CI, README, PRD, architecture docs, and contributor instructions.

## PR 2: Ingestion

Connector abstraction, local JSON ingestion, RSS ingestion, raw document persistence, fixtures, and tests.

## PR 3: Preprocessing

Cleaning, normalization, hashing, deduplication, processed document persistence, and tests.

## PR 4: LLM Abstraction

Provider boundary, mock client, prompt versions, structured parser, token/model logging, and tests.

## PR 5: Structured Analysis

Sentiment, viewpoint, risk extraction, evidence traceability, validated persistence, and tests.

## PR 6: Risk Scoring and Trends

Risk formula, trend aggregation, risk ranking, source-backed explanations, and tests.

## PR 7: Reporting

Markdown and HTML reports, templates, report artifacts, and deterministic output tests.

## PR 8: PDF Export

PDF rendering and artifact validation.

## PR 9: FastAPI Resources

Routes for sources, documents, analysis runs, risks, and reports.

## PR 10: Dashboard Expansion

Risk overview, source explorer, evidence drill-down, analysis runs, and report archive.

## PR 11: Scheduling

Daily CLI pipeline, scheduler integration, idempotent runs, and Docker service support.

## PR 12+: Evaluation and Research Docs

Gold dataset, baselines, metrics, error analysis, methodology, limitations, and final deployment docs.
