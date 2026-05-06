# Agentic Policy Brief Builder

Agentic Policy Brief Builder is a Streamlit Agentic RAG demo that helps reviewers turn local policy documents into cited policy brief drafts with evidence retrieval, citation audit, deterministic evals, and portfolio-ready quality gates.

> **Status:** Portfolio-ready demo. This project is intentionally scoped as a public portfolio artifact, not a production policy-analysis system.

## Synthetic-data disclosure

Public demos should use the synthetic Riverton policy packet in `data/synthetic/policy_packet/`. The packet is fictional and covers local housing affordability and zoning reform for a fictional city.

This repository does **not** include private customer data, employer data, confidential records, production exports, real policy case files, or committed secrets. Synthetic data is useful for safe demonstration and deterministic evaluation, but it does not prove performance on real policy documents.

## Business problem and product value

Policy teams often need to synthesize long memos, public comments, timelines, and option papers into concise decision briefs. Manual synthesis is slow, and citation tracking can be fragile.

This project demonstrates an AI-assisted workflow that keeps source evidence visible: retrieve relevant evidence, draft a structured brief, audit citations, and export Markdown for review.

See [`docs/portfolio_overview.md`](docs/portfolio_overview.md) for business framing, target users, demo workflow, and architecture notes. For a complete public demo path, start with [`docs/demo_walkthrough.md`](docs/demo_walkthrough.md).

## Features

- Streamlit UI for a synthetic policy packet or uploaded TXT/PDF documents.
- Document loading, text chunking, local retrieval, and cited policy brief drafting.
- Structured brief sections for key findings, policy options, risks/tradeoffs, recommendations, and evidence notes.
- Citation audit that checks whether cited evidence IDs map back to retrieved evidence.
- Markdown formatting and download support for briefs, retrieved evidence, and audit context.
- Deterministic local evals using synthetic fixtures and fake clients.
- CI gates for linting, tests, local evals, repository health, and release readiness.
- Public documentation for release notes, portfolio review, interview preparation, limitations, and roadmap.

## Architecture summary

```text
Streamlit app
  -> synthetic packet loader or TXT/PDF upload loader
  -> document chunking
  -> local vector retrieval
  -> citation-aware brief drafting
  -> citation audit
  -> Markdown formatting/export
```

Reusable application code lives under `src/agentic_policy_brief_builder/`:

| Package | Responsibility |
|---|---|
| `ingestion` | Load synthetic, TXT, and PDF documents; chunk records for retrieval. |
| `retrieval` | Create embeddings, index chunks, and retrieve relevant evidence. |
| `drafting` | Build structured policy brief drafts from policy questions and evidence. |
| `audit` | Validate citation references against retrieved evidence IDs. |
| `ui` | Format briefs, evidence, and audit results for Streamlit/Markdown display. |
| `evals` | Run deterministic local evaluation fixtures and quality gates. |
| `health` | Check repository health and release readiness. |

## Quickstart

### 1. Create a local environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configure the interactive app

Copy `.env.example` to `.env` and add your own local values. Do not commit `.env`.

```bash
cp .env.example .env
```

The Streamlit app can use environment variables, `.env`, or local Streamlit secrets. Required and optional variables are documented in `.env.example`:

| Variable | Required for interactive app | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key for model and embedding requests in the live Streamlit workflow. |
| `OPENAI_MODEL` | No | Chat/model name for policy brief generation. |
| `OPENAI_EMBEDDING_MODEL` | No | Embedding model name for retrieval. |
| `APP_ENV` | No | App environment such as `local`, `test`, `staging`, or `production`. |
| `VECTOR_STORE_DIR` | No | Local vector-store persistence directory. |

The deterministic tests, local evals, CI gates, repository-health check, and release-readiness check do **not** require a real `OPENAI_API_KEY` and do **not** make live OpenAI API calls.

### 3. Run the app

```bash
python -m streamlit run app/streamlit_app.py
```

In the UI, choose **Use synthetic policy packet** for the safest public demo path, enter a policy question, generate the cited brief, review retrieved evidence and citation audit, then download Markdown output if desired.

## Local validation commands

Run these checks from the repository root before opening a pull request or featuring the project:

```bash
python -m ruff check .
python -m pytest
python scripts/run_local_evals.py
python scripts/check_repo_health.py
python scripts/check_release_readiness.py
```

## Local eval commands

The local eval runner uses `evals/fixtures/synthetic_policy_questions.json`, deterministic fake clients, and the synthetic Riverton packet.

```bash
python scripts/run_local_evals.py
```

To run a custom fixture file:

```bash
python scripts/run_local_evals.py --fixture-path path/to/fixtures.json
```

See [`docs/evaluation.md`](docs/evaluation.md) for fixture behavior, checked gates, and evaluation limits.

## CI and quality gates

GitHub Actions runs the `CI` workflow for pull requests to `main`, pushes to `main`, and manual dispatches. The workflow installs dependencies and runs:

1. Ruff linting;
2. pytest;
3. deterministic local evals;
4. repository-health checks;
5. release-readiness checks.

CI intentionally does not require `OPENAI_API_KEY`, does not configure secrets, and does not make live OpenAI API calls. See [`docs/ci.md`](docs/ci.md) for details and matching local commands.

## Repository health and release readiness

This repo includes deterministic offline checks for public portfolio review:

```bash
python scripts/check_repo_health.py
python scripts/check_release_readiness.py
```

The checks verify required files, source package directories, test coverage entrypoints, scripts, CI wiring, synthetic-data disclosure, public-readiness docs, and the absence of obvious generated artifacts or secret-bearing files. They do not create tags, publish packages, deploy infrastructure, or create GitHub releases.

See [`docs/release_readiness.md`](docs/release_readiness.md) and [`docs/release_notes.md`](docs/release_notes.md) for the release-readiness checklist and first portfolio-ready release notes.

## Documentation guide

### Final portfolio path

Start here when preparing a public portfolio demo, recruiter review, or GitHub profile entry:

- [`docs/demo_walkthrough.md`](docs/demo_walkthrough.md): end-to-end Streamlit demo flow for synthetic packet and TXT/PDF upload paths.
- [`docs/profile_readme_entry.md`](docs/profile_readme_entry.md): concise copy-ready project entry for a GitHub profile README.
- [`docs/recruiter_summary.md`](docs/recruiter_summary.md): hiring-manager-friendly summary of the project and technical strengths.
- [`docs/technical_deep_dive.md`](docs/technical_deep_dive.md): readable architecture and implementation explanation.
- [`docs/demo_script.md`](docs/demo_script.md): 3-minute and 7-minute walkthrough scripts with likely Q&A.
- [`docs/screenshot_guide.md`](docs/screenshot_guide.md): recommended portfolio screenshots, captions, and synthetic-data disclosure guidance.
- [`docs/final_portfolio_checklist.md`](docs/final_portfolio_checklist.md): final public-readiness, validation, CI, release-readiness, and hygiene checklist.

### Existing project docs

- [`docs/portfolio_overview.md`](docs/portfolio_overview.md): business problem, product value, target user, workflow, and architecture.
- [`docs/release_notes.md`](docs/release_notes.md): first portfolio-ready release notes and validation gates.
- [`docs/interview_talk_track.md`](docs/interview_talk_track.md): concise project pitch, technical highlights, and likely interview questions.
- [`docs/limitations.md`](docs/limitations.md): demo boundaries, synthetic-data limits, eval limits, and production requirements.
- [`docs/roadmap.md`](docs/roadmap.md): realistic near-, medium-, and long-term enhancements.
- [`docs/evaluation.md`](docs/evaluation.md): deterministic local eval design.
- [`docs/ci.md`](docs/ci.md): CI behavior and local equivalents.

## Limitations

- This is a portfolio demo, not a production-ready policy-analysis platform.
- Synthetic data keeps public demos safe but does not prove real-world accuracy.
- Deterministic fake-client evals catch regressions but do not measure live model quality or expert policy judgment.
- Citation audit checks evidence-ID grounding, not full factual correctness or policy soundness.
- Real policy use would require expert review, stronger evaluation, monitoring, access control, privacy controls, audit logging, and governance.

See [`docs/limitations.md`](docs/limitations.md) for a fuller explanation.

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md) for realistic enhancements aligned with the current architecture.

## Security and responsible use

Do not commit `.env`, Streamlit secrets, API keys, private keys, credentials, private customer data, employer data, confidential records, or production exports. Use `.env.example` as the configuration template.

This project is a document-grounded research aid for educational and portfolio demonstration. It should not be used to create deceptive, malicious, privacy-invasive, credential-stealing, exploit-generating, surveillance, spam, or security-sensitive tooling. It does not provide legal, regulatory, lobbying, financial, or public-policy advice.

See [`SECURITY.md`](SECURITY.md) for supported reporting expectations.

## Changelog and release notes

- [`CHANGELOG.md`](CHANGELOG.md) tracks notable changes.
- [`docs/release_notes.md`](docs/release_notes.md) describes the first portfolio-ready release.

No GitHub release, tag, package publication, hosted deployment, or artifact publication is created by this documentation update.

## License

MIT. See [`LICENSE`](LICENSE).

## Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agentic-policy-brief-builder-m2m32uagba6zjainkf8kkc.streamlit.app)

Live Streamlit app: https://agentic-policy-brief-builder-m2m32uagba6zjainkf8kkc.streamlit.app

Public demo uses synthetic data for portfolio demonstration purposes.
