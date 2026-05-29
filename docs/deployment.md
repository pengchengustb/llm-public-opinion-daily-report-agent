# Deployment

## Local Docker Compose

Build and run both services:

```bash
docker compose up --build
```

Backend: <http://localhost:8000>

Dashboard: <http://localhost:8501>

Stop services:

```bash
docker compose down
```

## Environment

Copy `.env.example` to `.env` for local development. Do not commit real secrets.

## Current Persistence

PR #1 uses SQLite by default. The database file is mounted through `./data` when running Docker Compose. PostgreSQL can be added in a later persistence hardening PR.
