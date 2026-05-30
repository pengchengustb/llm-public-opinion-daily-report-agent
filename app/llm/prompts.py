"""Prompt version identifiers and high-level prompt policies."""

STRUCTURED_ANALYSIS_PROMPT_VERSION = "structured-analysis-v0.1-mock-ready"
DAILY_REPORT_PROMPT_VERSION = "daily-report-v0.1-foundation"

STRUCTURED_ANALYSIS_SYSTEM_POLICY = (
    "You are a public opinion monitoring analyst. Produce Chinese user-facing text. "
    "Return only schema-valid JSON. Use only supplied evidence IDs. Mark uncertainty "
    "explicitly. Do not invent sources, dates, quotes, or unsupported claims."
)

DAILY_REPORT_SYSTEM_POLICY = STRUCTURED_ANALYSIS_SYSTEM_POLICY
