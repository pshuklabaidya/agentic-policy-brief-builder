from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agentic_policy_brief_builder.health import check_repository_health
from agentic_policy_brief_builder.health.repository import (
    REQUIRED_PROJECT_FILES,
    REQUIRED_SCRIPTS,
    REQUIRED_SOURCE_PACKAGE_DIRS,
    REQUIRED_SYNTHETIC_DATA_DIRS,
    REQUIRED_TEST_FILES,
)


def create_minimal_repository(root: Path) -> None:
    for relative_path in REQUIRED_PROJECT_FILES:
        _write(root / relative_path, _content_for(relative_path))
    for relative_path in REQUIRED_SOURCE_PACKAGE_DIRS:
        (root / relative_path).mkdir(parents=True, exist_ok=True)
    for relative_path in REQUIRED_TEST_FILES:
        _write(root / relative_path, "def test_placeholder():\n    assert True\n")
    for relative_path in REQUIRED_SCRIPTS:
        _write(root / relative_path, "print('ok')\n")
    for relative_path in REQUIRED_SYNTHETIC_DATA_DIRS:
        (root / relative_path).mkdir(parents=True, exist_ok=True)
    _write(
        root / ".github/workflows/ci.yml",
        (
            "run: python -m ruff check .\n"
            "run: python -m pytest\n"
            "run: python scripts/run_local_evals.py\n"
        ),
    )


def test_repository_health_passes_for_minimal_project_tree(tmp_path: Path) -> None:
    create_minimal_repository(tmp_path)

    result = check_repository_health(tmp_path)

    assert result.passed is True
    assert result.findings == ()
    assert result.error_count == 0
    assert result.warning_count == 0
    assert "README.md" in result.checked_paths
    assert result.missing_paths == ()


def test_repository_health_reports_missing_required_files(tmp_path: Path) -> None:
    create_minimal_repository(tmp_path)
    (tmp_path / "README.md").unlink()

    result = check_repository_health(tmp_path)

    assert result.passed is False
    assert "README.md" in result.missing_paths
    assert any(
        finding.code == "missing_required_path" and finding.path == "README.md"
        for finding in result.findings
    )


def test_repository_health_detects_generated_artifacts(tmp_path: Path) -> None:
    create_minimal_repository(tmp_path)
    _write(tmp_path / "src/agentic_policy_brief_builder/__pycache__/module.cpython-312.pyc", "")

    result = check_repository_health(tmp_path)

    assert result.passed is False
    assert any(finding.code == "generated_artifact_committed" for finding in result.findings)


def test_repository_health_detects_secret_bearing_files(tmp_path: Path) -> None:
    create_minimal_repository(tmp_path)
    _write(tmp_path / ".env", "OPENAI_API_KEY=sk-not-a-real-key\n")

    result = check_repository_health(tmp_path)

    assert result.passed is False
    assert any(finding.code == "secret_file_committed" for finding in result.findings)


def test_repository_health_output_ordering_is_deterministic(tmp_path: Path) -> None:
    create_minimal_repository(tmp_path)
    (tmp_path / "README.md").unlink()
    (tmp_path / "LICENSE").unlink()
    _write(tmp_path / ".env", "token=value\n")
    _write(tmp_path / ".pytest_cache/README.md", "generated\n")

    first = check_repository_health(tmp_path)
    second = check_repository_health(tmp_path)

    assert first == second
    assert list(first.findings) == sorted(
        first.findings,
        key=lambda item: (item.path or "", item.severity.value, item.code, item.message),
    )


def test_repository_health_cli_exits_zero_for_current_repository() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_repo_health.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Repository health: PASSED" in completed.stdout


def _content_for(relative_path: str) -> str:
    if relative_path == "README.md":
        return "# Agentic RAG Policy Brief Builder\n\nSynthetic data. Setup. docs/ci.md.\n"
    return f"# {relative_path}\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
