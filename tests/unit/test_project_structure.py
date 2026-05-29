"""Dependency-light checks for the PR #1 project scaffold."""

from pathlib import Path


def test_foundation_files_exist() -> None:
    required_paths = [
        Path("pyproject.toml"),
        Path(".env.example"),
        Path("docker-compose.yml"),
        Path("app/main.py"),
        Path("dashboard/Home.py"),
        Path("docs/PRD.md"),
        Path("docs/architecture.md"),
    ]

    missing = [str(path) for path in required_paths if not path.exists()]

    assert missing == []


def test_readme_documents_core_run_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "uvicorn app.main:app" in readme
    assert "streamlit run dashboard/Home.py" in readme
    assert "docker compose up --build" in readme
