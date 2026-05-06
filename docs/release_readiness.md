# Repository Health and Release Readiness

This repository includes deterministic, offline checks that help keep the Agentic Policy Brief Builder portfolio-ready without adding deployment, publishing automation, hosted evals, or live model calls.

## Repository-health checks

Repository-health checks verify that the expected project structure is present and that the repo does not include obvious local-only or sensitive files. The checker validates:

- required project files such as `README.md`, `pyproject.toml`, `requirements.txt`, `.env.example`, `LICENSE`, `SECURITY.md`, `docs/ci.md`, and `docs/evaluation.md`;
- required source package directories for ingestion, retrieval, drafting, citation audit, evals, and UI code;
- required test files for the core offline RAG workflow;
- required scripts, including local evals and the health/readiness CLIs;
- a GitHub Actions CI workflow;
- the `data/synthetic/` directory;
- absence of obvious generated artifacts such as Python caches, local virtual environments, coverage files, build folders, and local vector-store folders;
- absence of obvious secret-bearing files such as `.env`, Streamlit secrets, private keys, token files, and credential files.

## Release-readiness checks

Release-readiness checks run repository-health checks first and then validate that the public-facing repo is understandable and safe to evaluate. The checker verifies:

- the README contains a clear Agentic RAG policy brief project description;
- the README preserves a synthetic-data disclosure;
- the README includes setup or quickstart instructions;
- the README includes local validation commands or links to validation documentation;
- the README links to CI or quality-gate documentation;
- evaluation, CI, release-readiness, release-notes, portfolio-overview, interview talk-track, limitations, and roadmap documentation exists;
- the deterministic local eval script exists;
- the CI workflow includes Ruff, pytest, and deterministic local eval commands;
- tests, CI, local evals, and these health checks do not require a real `OPENAI_API_KEY`.

## Deterministic and offline by design

Both checks inspect local files only. They do not call hosted OpenAI services, do not require network access, do not create releases, and do not publish artifacts. They produce sorted structured findings so output ordering is stable across runs.

The Streamlit app can use an OpenAI API key for interactive model-backed demos, but repository-health checks, release-readiness checks, tests, CI, and deterministic local evals do **not** require a real OpenAI API key.

## Local commands

Run repository-health checks from the repository root:

```bash
python scripts/check_repo_health.py
```

Run full release-readiness checks from the repository root:

```bash
python scripts/check_release_readiness.py
```

Both scripts print a concise summary. They exit with code `0` when no error-level findings exist and code `1` when any error-level finding exists.
