# Demo Workflow

This project can be demonstrated without network access or secrets because the default workflow uses deterministic sample data and mock LLM analysis.

## One-command Validation

```bash
python -m app validate-demo --date 2026-05-30
```

This command runs the daily workflow, generates Markdown and HTML reports, runs mock evaluation, checks artifact existence and metric thresholds, then writes a final validation report under `reports/validation/`.

## Manual Demo

```bash
python -m app run-daily --seed-sample --date 2026-05-30
python -m app evaluate-mock
python -m app api
streamlit run dashboard/app.py
```

Open:

- Backend: `http://localhost:8000`
- Dashboard: `http://localhost:8501`

Recommended dashboard path:

1. Confirm backend status is `ok`.
2. Review sentiment distribution, risk ranking, topic ranking, and evidence.
3. Open the report archive page for `2026-05-30`.
4. Download the generated Markdown or HTML daily report.
5. Open `reports/evaluation/evaluation_report.md`.
6. Open `reports/validation/final_validation_2026-05-30.md`.

## Portfolio Talking Points

- The system preserves evidence IDs from ingestion through report generation.
- Real LLM calls are isolated behind `app/llm` and intentionally disabled in mock mode.
- Deterministic tests and evaluation make the project CI-friendly.
- The dashboard uses backend APIs rather than provider SDKs or direct database access.
- Runtime data, generated reports, logs, and validation artifacts stay out of Git.
