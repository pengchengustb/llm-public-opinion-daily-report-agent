# AGENTS.md

## Project

This repository builds an LLM Public Opinion Daily Report Agent.

The agent should:
- ingest daily news articles and user comments
- summarize core viewpoints and arguments
- classify positive, neutral, and negative sentiment
- detect public relations risks
- generate actionable recommendations
- export daily reports in Markdown and PDF

## Working style

- Work in small milestones.
- Prefer one milestone per pull request.
- Before coding a large change, produce a plan.
- Do not make large architectural changes without explaining them.
- Keep the implementation simple and suitable for an MVP.

## Tech stack

- Python 3.11+
- pydantic for schemas
- typer for CLI
- pytest for tests
- Jinja2 for Markdown report rendering
- Markdown as the canonical report format
- PDF export can be implemented after Markdown reporting works

## Repository expectations

- Add or update tests for new behavior.
- Run pytest before considering work complete.
- Update README when changing user-facing commands.
- Keep OpenAI API calls isolated in one module.
- Never hard-code API keys.
- Use `.env.example` for environment variable documentation.

## Product constraints

- Start with local sample data.
- Do not implement complex scraping in the MVP.
- Do not add a web dashboard until the CLI pipeline works.
- Keep each analysis output traceable to source article/comment IDs.

## Report requirements

The daily report should include:
1. Executive summary
2. Data overview
3. Key news summary
4. Major public viewpoints
5. Sentiment distribution
6. Risk analysis
7. Actionable recommendations
8. Appendix / limitations

## Definition of done

A milestone is done only when:
- the relevant CLI command works
- pytest passes
- generated files are saved in the expected location
- README or docs are updated if needed
- the final response summarizes changed files and validation results
