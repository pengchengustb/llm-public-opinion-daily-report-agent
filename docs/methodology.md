# Methodology

## Data Pipeline

1. Ingest documents from local JSON/CSV and RSS connectors.
2. Validate required fields and normalize timestamps.
3. Clean text while retaining source IDs and original raw text.
4. Deduplicate by stable content hashes.
5. Persist records and data quality summaries.

Current implementation supports deterministic local JSON/CSV/RSS ingestion through CLI commands and records data quality issues as first-class database rows. Language detection is intentionally lightweight and dependency-free; later PRs may replace it if evaluation shows the heuristic is insufficient.

## Analysis Pipeline

1. Select article/comment evidence for a run.
2. Generate structured sentiment, viewpoint, topic, risk, and recommendation outputs.
3. Validate every LLM response with Pydantic contracts.
4. Store analysis outputs with prompt versions and evidence IDs.
5. Combine deterministic metrics with LLM explanations.

Current implementation uses deterministic mock analysis so tests and CI do not require network access or secrets. Real OpenAI integration must keep the same contracts and remain isolated under `app/llm`.

## Risk Scoring Direction

Later PRs will calculate:

- Negative sentiment ratio.
- Topic growth.
- High-engagement negative comments.
- Sensitive-topic score.
- Misinformation or uncertainty score.
- Combined deterministic risk score with Chinese explanation.

## Evidence Traceability

Every insight must cite source, article, or comment evidence IDs. Unsupported conclusions should be rejected or marked uncertain.
