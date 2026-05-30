# Evaluation Design

## Evaluation Targets

- Sentiment classification.
- Risk classification.
- Viewpoint extraction.
- Report quality.
- System reliability.

## Metrics

Sentiment:

- Accuracy.
- Macro F1.
- Per-class precision and recall.

Risk:

- Macro F1.
- Severity agreement.
- Evidence citation coverage.

Viewpoints:

- Viewpoint coverage.
- Evidence overlap.
- Label or semantic match where practical.

Reports:

- Completeness.
- Evidence traceability.
- Risk/action alignment.
- Unsupported-claim count.

## Implemented Mock Evaluation

The deterministic mock evaluation is available through:

```bash
python -m app evaluate-mock
```

It evaluates built-in gold cases for sentiment labels, risk severity, evidence citation coverage, and report completeness. Results are persisted to `evaluation_runs` and `evaluation_metrics`, then written as JSON metrics and `evaluation_report.md` under `REPORT_OUTPUT_DIR/evaluation`.

## Artifacts

The current implementation generates:

- `evaluation_report.md`.
- JSON metrics artifacts.
- Reproducible mock-mode evaluation output for CI.
