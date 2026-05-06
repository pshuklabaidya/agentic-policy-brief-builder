from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agentic_policy_brief_builder.health import check_release_readiness
from tests.test_repository_health import create_minimal_repository

README = """# Agentic RAG Policy Brief Builder

Agentic Policy Brief Builder is an Agentic RAG policy brief project for cited policy analysis.

## Synthetic-Data Disclosure

This demo uses synthetic data only.

## Quickstart

Install dependencies and run the app.

## Local validation

Run `python -m ruff check .`, `python -m pytest`, and `python scripts/run_local_evals.py`.
See `docs/ci.md` for continuous integration and quality gate details.
"""

CI = """name: CI
steps:
  - run: python -m ruff check .
  - run: python -m pytest
  - run: python scripts/run_local_evals.py
"""


def create_release_ready_repository(root: Path) -> None:
    create_minimal_repository(root)
    _write(root / "README.md", README)
    _write(
        root / "docs/release_readiness.md",
        "# Release readiness\nOffline deterministic checks.\n",
    )
    _write(root / ".github/workflows/ci.yml", CI)
    _write(root / "scripts/run_local_evals.py", "print('deterministic local evals')\n")


def test_release_readiness_passes_for_minimal_project_tree(tmp_path: Path) -> None:
    create_release_ready_repository(tmp_path)

    result = check_release_readiness(tmp_path)

    assert result.passed is True
    assert result.findings == ()
    assert result.error_count == 0
    assert "docs/release_readiness.md" in result.checked_paths


def test_release_readiness_reports_missing_readme_disclosure(tmp_path: Path) -> None:
    create_release_ready_repository(tmp_path)
    _write(
        tmp_path / "README.md",
        "# Agentic RAG Policy Brief Builder\n\nSetup instructions. See docs/ci.md.\n",
    )

    result = check_release_readiness(tmp_path)

    assert result.passed is False
    assert any(
        finding.code == "readme_missing_synthetic_data_disclosure" for finding in result.findings
    )


def test_release_readiness_reports_missing_ci_gates(tmp_path: Path) -> None:
    create_release_ready_repository(tmp_path)
    _write(tmp_path / ".github/workflows/ci.yml", "name: CI\nsteps:\n  - run: echo ok\n")

    result = check_release_readiness(tmp_path)

    assert result.passed is False
    codes = {finding.code for finding in result.findings}
    assert {"ci_missing_ruff", "ci_missing_pytest", "ci_missing_local_evals"} <= codes


def test_release_readiness_output_ordering_is_deterministic(tmp_path: Path) -> None:
    create_release_ready_repository(tmp_path)
    (tmp_path / "README.md").unlink()
    _write(tmp_path / ".github/workflows/ci.yml", "name: CI\n")

    first = check_release_readiness(tmp_path)
    second = check_release_readiness(tmp_path)

    assert first == second
    assert list(first.findings) == sorted(
        first.findings,
        key=lambda item: (item.path or "", item.severity.value, item.code, item.message),
    )


def test_release_readiness_cli_exits_zero_for_current_repository() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_release_readiness.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Release readiness: PASSED" in completed.stdout


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
