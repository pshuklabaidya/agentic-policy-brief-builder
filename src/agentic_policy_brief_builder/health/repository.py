"""Deterministic repository health checks for portfolio readiness."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class HealthCheckSeverity(StrEnum):
    """Severity levels emitted by health checks."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, order=True)
class HealthCheckFinding:
    """A deterministic, structured health-check finding."""

    severity: HealthCheckSeverity
    code: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class HealthCheckResult:
    """Structured result returned by repository and release checks."""

    passed: bool
    findings: tuple[HealthCheckFinding, ...] = field(default_factory=tuple)
    checked_paths: tuple[str, ...] = field(default_factory=tuple)
    missing_paths: tuple[str, ...] = field(default_factory=tuple)
    warning_count: int = 0
    error_count: int = 0


REQUIRED_PROJECT_FILES: tuple[str, ...] = (
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    ".env.example",
    "LICENSE",
    "SECURITY.md",
    "docs/ci.md",
    "docs/evaluation.md",
)

REQUIRED_SOURCE_PACKAGE_DIRS: tuple[str, ...] = (
    "src/agentic_policy_brief_builder/ingestion",
    "src/agentic_policy_brief_builder/retrieval",
    "src/agentic_policy_brief_builder/drafting",
    "src/agentic_policy_brief_builder/audit",
    "src/agentic_policy_brief_builder/evals",
    "src/agentic_policy_brief_builder/ui",
)

REQUIRED_TEST_FILES: tuple[str, ...] = (
    "tests/test_loaders.py",
    "tests/test_chunking.py",
    "tests/test_vector_store.py",
    "tests/test_brief_drafting.py",
    "tests/test_citation_audit.py",
    "tests/test_eval_runner.py",
    "tests/test_repository_health.py",
    "tests/test_release_readiness.py",
)

REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/run_local_evals.py",
    "scripts/check_repo_health.py",
    "scripts/check_release_readiness.py",
)

REQUIRED_CI_WORKFLOWS: tuple[str, ...] = (
    ".github/workflows/ci.yml",
    ".github/workflows/ci.yaml",
)

REQUIRED_SYNTHETIC_DATA_DIRS: tuple[str, ...] = ("data/synthetic",)

GENERATED_ARTIFACT_NAMES: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        ".chroma",
        ".venv",
        "venv",
        "build",
        "dist",
    }
)
GENERATED_ARTIFACT_SUFFIXES: tuple[str, ...] = (".pyc", ".pyo", ".egg-info")

SECRET_FILE_NAMES: frozenset[str] = frozenset(
    {
        ".env",
        "secrets.toml",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
    }
)
SECRET_FILE_SUFFIXES: tuple[str, ...] = (".pem", ".key", ".p12", ".pfx")
SECRET_FILE_SUBSTRINGS: tuple[str, ...] = ("secret", "credential", "token")

IGNORED_SCAN_DIRS: frozenset[str] = frozenset({".git", ".tox", ".nox", "node_modules"})


def check_repository_health(root: str | Path = ".") -> HealthCheckResult:
    """Check that a repository has required files and no obvious unsafe artifacts."""

    root_path = Path(root).resolve()
    findings: list[HealthCheckFinding] = []
    checked_paths: set[str] = set()
    missing_paths: set[str] = set()

    required_exact_paths = (
        REQUIRED_PROJECT_FILES
        + REQUIRED_SOURCE_PACKAGE_DIRS
        + REQUIRED_TEST_FILES
        + REQUIRED_SCRIPTS
        + REQUIRED_SYNTHETIC_DATA_DIRS
    )
    for relative_path in required_exact_paths:
        checked_paths.add(relative_path)
        if not (root_path / relative_path).exists():
            missing_paths.add(relative_path)
            findings.append(
                HealthCheckFinding(
                    severity=HealthCheckSeverity.ERROR,
                    code="missing_required_path",
                    message=f"Required path is missing: {relative_path}",
                    path=relative_path,
                )
            )

    checked_paths.update(REQUIRED_CI_WORKFLOWS)
    if not any((root_path / path).is_file() for path in REQUIRED_CI_WORKFLOWS):
        missing_paths.update(REQUIRED_CI_WORKFLOWS)
        findings.append(
            HealthCheckFinding(
                severity=HealthCheckSeverity.ERROR,
                code="missing_ci_workflow",
                message=(
                    "A GitHub Actions CI workflow is required at "
                    ".github/workflows/ci.yml or .yaml."
                ),
                path=".github/workflows",
            )
        )

    for relative_path in _iter_scannable_paths(root_path):
        checked_paths.add(relative_path)
        artifact_reason = _generated_artifact_reason(relative_path)
        if artifact_reason:
            findings.append(
                HealthCheckFinding(
                    severity=HealthCheckSeverity.ERROR,
                    code="generated_artifact_committed",
                    message=f"Obvious local generated artifact detected ({artifact_reason}).",
                    path=relative_path,
                )
            )

        secret_reason = _secret_file_reason(relative_path)
        if secret_reason:
            findings.append(
                HealthCheckFinding(
                    severity=HealthCheckSeverity.ERROR,
                    code="secret_file_committed",
                    message=f"Obvious secret-bearing file detected ({secret_reason}).",
                    path=relative_path,
                )
            )

    return _build_result(findings, checked_paths, missing_paths)


def format_health_check_result(title: str, result: HealthCheckResult) -> str:
    """Return a readable deterministic summary for a health-check result."""

    status = "PASSED" if result.passed else "FAILED"
    lines = [
        f"{title}: {status}",
        f"Errors: {result.error_count}",
        f"Warnings: {result.warning_count}",
        f"Checked paths: {len(result.checked_paths)}",
        f"Missing paths: {len(result.missing_paths)}",
    ]
    if result.findings:
        lines.append("Findings:")
        for finding in result.findings:
            path_suffix = f" [{finding.path}]" if finding.path else ""
            lines.append(
                f"- {finding.severity.value.upper()} {finding.code}{path_suffix}: {finding.message}"
            )
    else:
        lines.append("Findings: none")
    return "\n".join(lines)


def _build_result(
    findings: Iterable[HealthCheckFinding],
    checked_paths: Iterable[str],
    missing_paths: Iterable[str],
) -> HealthCheckResult:
    ordered_findings = tuple(
        sorted(
            findings,
            key=lambda item: (item.path or "", item.severity.value, item.code, item.message),
        )
    )
    warning_count = sum(
        1 for finding in ordered_findings if finding.severity == HealthCheckSeverity.WARNING
    )
    error_count = sum(
        1 for finding in ordered_findings if finding.severity == HealthCheckSeverity.ERROR
    )
    return HealthCheckResult(
        passed=error_count == 0,
        findings=ordered_findings,
        checked_paths=tuple(sorted(set(checked_paths))),
        missing_paths=tuple(sorted(set(missing_paths))),
        warning_count=warning_count,
        error_count=error_count,
    )


def _iter_scannable_paths(root: Path) -> Iterable[str]:
    tracked_paths = _git_tracked_paths(root)
    if tracked_paths is not None:
        for relative_path in tracked_paths:
            if not _is_ignored_scan_path(relative_path):
                yield relative_path
        return

    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative_path = path.relative_to(root).as_posix()
        if not _is_ignored_scan_path(relative_path):
            yield relative_path


def _git_tracked_paths(root: Path) -> tuple[str, ...] | None:
    if not (root / ".git").exists():
        return None
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return tuple(sorted(line for line in completed.stdout.splitlines() if line))


def _is_ignored_scan_path(relative_path: str) -> bool:
    return any(part in IGNORED_SCAN_DIRS for part in Path(relative_path).parts)


def _generated_artifact_reason(relative_path: str) -> str | None:
    parts = Path(relative_path).parts
    for part in parts:
        if part in GENERATED_ARTIFACT_NAMES:
            return part
        if any(part.endswith(suffix) for suffix in GENERATED_ARTIFACT_SUFFIXES):
            return part
    return None


def _secret_file_reason(relative_path: str) -> str | None:
    path = Path(relative_path)
    name = path.name
    lower_name = name.lower()
    if relative_path == ".env.example":
        return None
    if name in SECRET_FILE_NAMES:
        return name
    if any(lower_name.endswith(suffix) for suffix in SECRET_FILE_SUFFIXES):
        return name
    if ".streamlit" in path.parts and name == "secrets.toml":
        return ".streamlit/secrets.toml"
    if any(substring in lower_name for substring in SECRET_FILE_SUBSTRINGS):
        return name
    return None
