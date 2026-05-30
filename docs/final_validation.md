# Final Validation Checklist

Use this checklist before presenting or submitting the project.

## Environment

- Python dependencies installed with `python -m pip install -e ".[dev]"`.
- `.env` created from `.env.example` if local overrides are needed.
- `LLM_MOCK_MODE=true` unless real provider integration has been implemented.
- Runtime database and generated artifacts are under ignored directories.

## Quality Gates

```bash
ruff check .
pytest
python -m compileall app tests dashboard
```

Expected result:

- Ruff passes.
- pytest passes.
- compileall reports no syntax errors.

## Functional Demo

```bash
python -m app validate-demo --date 2026-05-30
```

Expected artifacts:

- `reports/2026-05-30/daily_report_2026-05-30.md`
- `reports/2026-05-30/daily_report_2026-05-30.html`
- `reports/automation_logs/*.json`
- `reports/evaluation/evaluation_report.md`
- `reports/validation/final_validation_2026-05-30.md`

## Dashboard

```bash
python -m app api
streamlit run dashboard/app.py
```

Expected behavior:

- Backend health is `ok`.
- Dashboard shows sentiment, risks, topics, and evidence.
- Report archive shows generated Markdown and HTML download buttons.

## Known Deferred Work

- Real OpenAI provider calls.
- Real web scraping beyond local files and RSS/XML feeds.
- PDF export.
- Production authentication, access control, and advanced dashboard drill-down.
