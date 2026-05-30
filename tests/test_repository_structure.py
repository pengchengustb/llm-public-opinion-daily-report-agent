from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_foundation_files_exist() -> None:
    required_paths = [
        "pyproject.toml",
        "README.md",
        "AGENTS.md",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        "docs/PRD.md",
        "docs/architecture.md",
        "docs/methodology.md",
        "docs/roadmap.md",
    ]

    missing = [path for path in required_paths if not (ROOT / path).exists()]
    assert missing == []


def test_planned_module_boundaries_exist() -> None:
    required_dirs = [
        "app/api",
        "app/core",
        "app/db",
        "app/ingestion",
        "app/preprocessing",
        "app/llm",
        "app/analysis",
        "app/risk",
        "app/reporting",
        "app/evaluation",
        "dashboard",
        "tests",
        "docs",
    ]

    missing = [path for path in required_dirs if not (ROOT / path).is_dir()]
    assert missing == []

