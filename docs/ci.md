# Continuous Integration

The repository uses a GitHub Actions workflow at `.github/workflows/ci.yml` named `CI` to run the same deterministic quality gates that developers can run locally.

## When CI runs

CI runs for:

- pull requests targeting the `main` branch;
- pushes to the `main` branch;
- manual runs started from the GitHub Actions `workflow_dispatch` control.

## What CI runs

The CI job runs on `ubuntu-latest` with Python 3.12 and a pip dependency cache. It checks out the repository, upgrades pip, installs `requirements.txt`, and then runs these gates in order:

1. Ruff linting;
2. the pytest test suite;
3. deterministic local evaluations;
4. repository-health checks;
5. release-readiness checks.

Any failing lint, test, required evaluation gate, repository-health check, or release-readiness check fails the workflow.

## Evaluation safety

The local evaluation gate is deterministic and synthetic-data-based. It uses the synthetic Riverton policy packet and deterministic fake clients rather than live model or embedding services.

CI intentionally does **not** require `OPENAI_API_KEY`, does not configure secrets, and does not make live OpenAI API calls. Hosted OpenAI evals and deployment checks are outside the scope of this workflow.

## Local developer commands

Run the same checks from the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ruff check .
python -m pytest
python scripts/run_local_evals.py
python scripts/check_repo_health.py
python scripts/check_release_readiness.py
```
