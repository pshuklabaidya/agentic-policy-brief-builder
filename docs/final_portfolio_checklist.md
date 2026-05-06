# Final Portfolio Checklist

Use this checklist before sharing the repository in a public portfolio, GitHub profile README, interview packet, or demo walkthrough.

## Public-readiness checks

- [ ] README clearly describes the Agentic RAG policy brief demo.
- [ ] Synthetic-data disclosure is visible and accurate.
- [ ] Limitations are explicit: this is not production-ready and not policy, legal, regulatory, lobbying, financial, or operational advice.
- [ ] The final portfolio docs are linked from the README.
- [ ] No GitHub tag, release, package publish, hosted deployment, or generated artifact is implied unless it actually exists.

## Documentation checks

- [ ] `docs/demo_walkthrough.md` explains synthetic and upload demo flows.
- [ ] `docs/profile_readme_entry.md` is copy-ready but does not modify a separate profile repository.
- [ ] `docs/recruiter_summary.md` is concise and hiring-manager friendly.
- [ ] `docs/technical_deep_dive.md` explains architecture, ingestion, chunking, evidence IDs, retrieval, drafting, audit, evals, CI, and release readiness.
- [ ] `docs/demo_script.md` includes 3-minute and 7-minute scripts.
- [ ] `docs/screenshot_guide.md` recommends screenshots without committing generated assets.
- [ ] `docs/final_portfolio_checklist.md` is current.
- [ ] Existing docs for CI, evaluation, limitations, roadmap, release notes, and release readiness remain accurate.

## Validation command checks

Run from the repository root:

```bash
python -m ruff check .
python -m pytest
python scripts/run_local_evals.py
python scripts/check_repo_health.py
python scripts/check_release_readiness.py
```

Confirm the commands pass before featuring the project.

## CI checks

- [ ] GitHub Actions `CI` workflow is present.
- [ ] CI runs Ruff, pytest, deterministic local evals, repository-health checks, and release-readiness checks.
- [ ] CI does not require `OPENAI_API_KEY` or configured secrets.
- [ ] CI does not make live OpenAI API calls.

## Release-readiness checks

- [ ] `python scripts/check_release_readiness.py` reports `Release readiness: PASSED`.
- [ ] Release-readiness docs explain that checks are deterministic and offline.
- [ ] Release notes do not claim a hosted deployment, package publish, tag, or GitHub release unless created intentionally outside this issue.

## Secret and artifact hygiene checks

- [ ] No `.env`, Streamlit secrets, API keys, private keys, credential files, or token files are committed.
- [ ] No private customer data, employer data, confidential records, production exports, or real policy case files are committed.
- [ ] No generated caches, local vector stores, build folders, coverage outputs, or virtual environments are committed.
- [ ] Screenshots are not committed unless intentionally small, approved, and free of sensitive content.

## Live Demo

Live Streamlit app: https://agentic-policy-brief-builder-m2m32uagba6zjainkf8kkc.streamlit.app

Public demo uses synthetic data for portfolio demonstration purposes.
