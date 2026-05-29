# Architecture

## Overview

The system is organized as a modular pipeline with API, dashboard, persistence, analysis, reporting, scheduling, and evaluation layers. PR #1 creates the foundation so later PRs can add behavior without restructuring the repository.

```text
Data Sources
   |
   v
Ingestion Connectors
   |
   v
Preprocessing and Deduplication
   |
   v
SQLModel Persistence
   |
   +--> FastAPI Backend
   +--> Streamlit Dashboard
   +--> Structured Analysis Layer
             |
             v
       Risk Scoring and Trends
             |
             v
       Daily Report Generation
             |
             v
       Evaluation Suite
```

## Backend

The backend lives under `app/` and exposes FastAPI routes. PR #1 provides `/health`; later PRs will add routes for sources, documents, analysis runs, risks, and reports.

## Configuration

`app/config/settings.py` centralizes environment configuration using Pydantic settings. `.env.example` documents safe local defaults. Real secrets must be supplied outside version control.

## Database

`app/db/models.py` defines initial SQLModel entities:

- `Source`
- `RawDocument`
- `ProcessedDocument`
- `AnalysisRun`

These models establish source traceability and run metadata before ingestion and analysis are implemented.

## Schemas

`app/schemas/analysis.py` defines structured analysis contracts for future LLM output:

- sentiment labels
- risk taxonomy
- evidence references
- viewpoint results
- risk finding results
- top-level structured analysis output

Every sentiment conclusion requires at least one source document ID.

## LLM Boundary

The `app/llm/` package is reserved for provider integration, prompt templates, mock mode, structured parsing, and token/model logging. Real LLM calls are not implemented in PR #1.

## Dashboard

The Streamlit dashboard lives under `dashboard/`. PR #1 provides a home page and placeholder pages that will be expanded as ingestion, analysis, reports, and evaluation land.

## Deployment

Docker Compose runs two services:

- `backend` on port `8000`
- `dashboard` on port `8501`

The compose stack uses local SQLite storage under `./data` for the foundation stage. A PostgreSQL service can be introduced when migrations and production persistence are added.
