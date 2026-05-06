"""Deterministic release-readiness checks for the repository."""

from __future__ import annotations

from pathlib import Path

from agentic_policy_brief_builder.health.repository import (
    HealthCheckFinding,
    HealthCheckResult,
    HealthCheckSeverity,
    _build_result,
    check_repository_health,
)

CI_WORKFLOW_PATHS: tuple[str, ...] = (".github/workflows/ci.yml", ".github/workflows/ci.yaml")
REQUIRED_CI_COMMAND_MARKERS: tuple[tuple[str, str], ...] = (
    ("ci_missing_ruff", "ruff"),
    ("ci_missing_pytest", "pytest"),
    ("ci_missing_local_evals", "scripts/run_local_evals.py"),
)


def check_release_readiness(root: str | Path = ".") -> HealthCheckResult:
    """Check repository health plus public release-readiness documentation and gates."""

    root_path = Path(root).resolve()
    repository_result = check_repository_health(root_path)
    findings: list[HealthCheckFinding] = []
    checked_paths: set[str] = set(repository_result.checked_paths)
    missing_paths: set[str] = set(repository_result.missing_paths)

    for finding in repository_result.findings:
        findings.append(
            HealthCheckFinding(
                severity=finding.severity,
                code=f"repository_{finding.code}",
                message=f"Repository health check failed: {finding.message}",
                path=finding.path,
            )
        )

    readme_path = root_path / "README.md"
    checked_paths.add("README.md")
    readme_text = _read_text(readme_path)
    if readme_text is None:
        missing_paths.add("README.md")
    else:
        _require_text(
            findings,
            readme_text,
            path="README.md",
            code="readme_missing_project_description",
            message="README should describe the Agentic RAG policy brief builder clearly.",
            required_terms=("agentic", "rag", "policy", "brief"),
        )
        _require_text(
            findings,
            readme_text,
            path="README.md",
            code="readme_missing_synthetic_data_disclosure",
            message="README should disclose that demo data is synthetic.",
            required_terms=("synthetic", "data"),
        )
        _require_any_text(
            findings,
            readme_text,
            path="README.md",
            code="readme_missing_setup_or_quickstart",
            message="README should include setup or quickstart instructions.",
            required_terms=("setup", "quickstart", "local configuration"),
        )
        _require_any_text(
            findings,
            readme_text,
            path="README.md",
            code="readme_missing_local_validation",
            message="README should include local validation commands or link to validation docs.",
            required_terms=("pytest", "ruff", "local eval", "docs/ci.md", "validation"),
        )
        _require_any_text(
            findings,
            readme_text,
            path="README.md",
            code="readme_missing_ci_quality_link",
            message="README should link to CI or quality-gate documentation.",
            required_terms=("docs/ci.md", "quality gate", "continuous integration"),
        )

    for relative_path, code, message in (
        ("docs/evaluation.md", "missing_evaluation_docs", "Evaluation documentation is required."),
        ("docs/ci.md", "missing_ci_docs", "CI documentation is required."),
        (
            "docs/release_readiness.md",
            "missing_release_readiness_docs",
            "Release-readiness documentation is required.",
        ),
        ("docs/release_notes.md", "missing_release_notes", "Release notes are required."),
        (
            "docs/portfolio_overview.md",
            "missing_portfolio_overview",
            "Portfolio overview documentation is required.",
        ),
        (
            "docs/interview_talk_track.md",
            "missing_interview_talk_track",
            "Interview talk-track documentation is required.",
        ),
        (
            "docs/limitations.md",
            "missing_limitations_docs",
            "Limitations documentation is required.",
        ),
        ("docs/roadmap.md", "missing_roadmap_docs", "Roadmap documentation is required."),
        (
            "scripts/run_local_evals.py",
            "missing_local_eval_script",
            "Deterministic local eval script is required.",
        ),
    ):
        checked_paths.add(relative_path)
        if not (root_path / relative_path).exists():
            missing_paths.add(relative_path)
            findings.append(
                HealthCheckFinding(
                    severity=HealthCheckSeverity.ERROR,
                    code=code,
                    message=message,
                    path=relative_path,
                )
            )

    ci_text, ci_path = _read_first_existing(root_path, CI_WORKFLOW_PATHS)
    checked_paths.update(CI_WORKFLOW_PATHS)
    if ci_text is None:
        findings.append(
            HealthCheckFinding(
                severity=HealthCheckSeverity.ERROR,
                code="missing_ci_workflow",
                message="CI workflow is required for release readiness.",
                path=".github/workflows",
            )
        )
    else:
        normalized_ci = ci_text.lower()
        for code, marker in REQUIRED_CI_COMMAND_MARKERS:
            if marker not in normalized_ci:
                findings.append(
                    HealthCheckFinding(
                        severity=HealthCheckSeverity.ERROR,
                        code=code,
                        message=f"CI workflow should include {marker}.",
                        path=ci_path,
                    )
                )
        if "openai_api_key" in normalized_ci:
            findings.append(
                HealthCheckFinding(
                    severity=HealthCheckSeverity.ERROR,
                    code="ci_requires_openai_api_key",
                    message="CI workflow should not require a real OPENAI_API_KEY.",
                    path=ci_path,
                )
            )

    for relative_path in ("tests", "scripts/run_local_evals.py"):
        checked_paths.add(relative_path)
        path = root_path / relative_path
        if path.exists() and _path_mentions_required_openai_key(path):
            findings.append(
                HealthCheckFinding(
                    severity=HealthCheckSeverity.ERROR,
                    code="local_checks_require_openai_api_key",
                    message="Tests and local evals must not require a real OPENAI_API_KEY.",
                    path=relative_path,
                )
            )

    return _build_result(findings, checked_paths, missing_paths)


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _read_first_existing(
    root: Path, relative_paths: tuple[str, ...]
) -> tuple[str | None, str | None]:
    for relative_path in relative_paths:
        text = _read_text(root / relative_path)
        if text is not None:
            return text, relative_path
    return None, None


def _require_text(
    findings: list[HealthCheckFinding],
    text: str,
    *,
    path: str,
    code: str,
    message: str,
    required_terms: tuple[str, ...],
) -> None:
    normalized = text.lower()
    if not all(term in normalized for term in required_terms):
        findings.append(
            HealthCheckFinding(
                severity=HealthCheckSeverity.ERROR,
                code=code,
                message=message,
                path=path,
            )
        )


def _require_any_text(
    findings: list[HealthCheckFinding],
    text: str,
    *,
    path: str,
    code: str,
    message: str,
    required_terms: tuple[str, ...],
) -> None:
    normalized = text.lower()
    if not any(term in normalized for term in required_terms):
        findings.append(
            HealthCheckFinding(
                severity=HealthCheckSeverity.ERROR,
                code=code,
                message=message,
                path=path,
            )
        )


def _path_mentions_required_openai_key(path: Path) -> bool:
    files = (
        [path]
        if path.is_file()
        else sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    )
    for file_path in files:
        if file_path.suffix not in {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml"}:
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
        if "openai_api_key" in text and any(
            phrase in text
            for phrase in (
                "required openai_api_key",
                "openai_api_key is required",
                "requires openai_api_key",
                "must set openai_api_key",
                "os.environ[\"openai_api_key\"]",
                "os.environ['openai_api_key']",
            )
        ):
            return True
    return False
