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

## Artifacts

Later PRs will generate:

- `evaluation_report.md`.
- JSON metrics artifacts.
- Reproducible mock-mode evaluation output for CI.

