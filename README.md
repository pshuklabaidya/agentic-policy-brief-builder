# Agentic Policy Brief Builder

Agentic Policy Brief Builder is a Streamlit-first Agentic RAG portfolio project for generating cited policy briefs from synthetic local policy documents. It demonstrates offline ingestion, chunking, retrieval, brief drafting, citation audit, deterministic local evaluation, and CI quality gates for a public, recruiter-friendly AI application.

> Status: Portfolio-ready Agentic RAG policy brief builder with deterministic offline tests and synthetic-data demos.

## Purpose

This template provides a consistent starting structure for AI portfolio repositories that demonstrate:

- Clear business problem framing
- Synthetic-data disclosure
- Streamlit-first demo design
- Reproducible setup instructions
- Tests and quality checks
- Evaluation notes
- Executive-polished documentation
- Responsible AI boundaries

## Intended Use

Use this template to create portfolio projects such as:

- Agentic RAG customer support assistant
- LLM evaluation harness
- Policy or financial document RAG assistant
- Product analytics copilot
- Compliance-aware document assistant
- AI workflow automation dashboard
- Synthetic business intelligence demo

## Template Principles

Every project created from this template should follow these principles:

- Use synthetic or public data only unless clear data rights exist.
- Label synthetic datasets clearly.
- Include setup instructions.
- Include tests.
- Include limitations.
- Include evaluation notes.

## Repository Structure

```text
.
├── app/
├── src/
├── tests/
├── data/synthetic/
├── docs/
├── evals/
├── scripts/
├── .github/workflows/
├── README.md
├── SECURITY.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Folder And File Guide

| Path | Purpose |
|---|---|
| `app/` | Streamlit app entrypoints and demo UI files |
| `src/` | Reusable application logic, RAG pipelines, agents, schemas, and utilities |
| `tests/` | Unit tests, smoke tests, and regression checks |
| `data/synthetic/` | Clearly labeled synthetic datasets used for demo workflows |
| `docs/` | Architecture notes, data dictionaries, diagrams, implementation notes, and evaluation summaries |
| `evals/` | Evaluation datasets, metrics scripts, and result summaries |
| `scripts/` | Data generation, ingestion, evaluation, and setup scripts |
| `.github/workflows/` | GitHub Actions workflows for tests and quality checks |

## Recommended Project README Pattern

Each generated project should replace this template README with a project-specific README containing:

- Project title
- One-sentence value proposition
- Demo status
- Synthetic-data disclosure
- Business problem
- Architecture overview
- Features
- Tech stack
- Quickstart
- Example usage
- Evaluation
- Tests
- Limitations
- Roadmap
- License

## Synthetic-Data Disclosure

Public demos for this project use synthetic data. The demo policy packet lives in `data/synthetic/policy_packet/` and covers the fictional topic of local housing affordability and zoning reform in the City of Riverton.

> This project uses synthetic data for educational and portfolio demonstration purposes. It does not contain private customer data, employer data, confidential records, or production exports.

## Recommended Tech Stack

Default stack:

- Python
- Streamlit
- Pandas
- Pytest
- Ruff
- GitHub Actions

Optional additions by project type:

- LangChain or LlamaIndex for RAG workflows
- Chroma or Qdrant for vector retrieval
- FastAPI for API-first demos
- Docker for stronger reproducibility
- MkDocs or GitHub Pages for expanded documentation


## Local Configuration

The Streamlit app reads configuration from environment variables, a local `.env` file, or Streamlit secrets. Environment variables take precedence over Streamlit secrets. Do not commit real secrets.

Required and optional variables are documented in `.env.example`:

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key used for model and embedding requests |
| `OPENAI_MODEL` | No | Chat/model name for policy brief generation |
| `OPENAI_EMBEDDING_MODEL` | No | Embedding model name for retrieval |
| `APP_ENV` | No | App environment: `local`, `test`, `staging`, or `production` |
| `VECTOR_STORE_DIR` | No | Local vector-store persistence directory |

PowerShell local setup:

```powershell
Copy-Item .env.example .env
notepad .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app\streamlit_app.py
```

For Streamlit Community Cloud or local Streamlit secrets, use `.streamlit/secrets.toml` and keep it out of git:

```toml
OPENAI_API_KEY = "sk-your-key"
OPENAI_MODEL = "gpt-5.5"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
APP_ENV = "local"
VECTOR_STORE_DIR = ".chroma"
```

The app shows a clear error message if `OPENAI_API_KEY` is missing.


## Continuous Integration

GitHub Actions runs the `CI` workflow for pull requests targeting `main`, pushes to `main`, and manual dispatches. The workflow runs Ruff, pytest, and deterministic synthetic-data local evaluation gates without requiring `OPENAI_API_KEY` or live OpenAI API calls. See `docs/ci.md` for details and matching local commands.


## Repository Health and Release Readiness

This project includes deterministic, offline repository-health and release-readiness checks for public portfolio review. They verify required files and package directories, CI and local eval wiring, release-readiness documentation, synthetic-data disclosure, and the absence of obvious local generated artifacts or secret-bearing files.

Run the checks locally from the repository root:

```bash
python scripts/check_repo_health.py
python scripts/check_release_readiness.py
```

These checks do not require a real `OPENAI_API_KEY`, do not make live OpenAI API calls, and do not publish releases. See `docs/release_readiness.md` for the full checklist.

## Quality Checklist

Before featuring any project created from this template:

- [ ] README explains the business problem clearly.
- [ ] Synthetic data is disclosed clearly.
- [ ] Setup instructions work from a fresh clone.
- [ ] Tests exist and pass.
- [ ] GitHub Actions workflow runs successfully.
- [ ] Limitations are explicit.
- [ ] Evaluation notes explain quality checks, metrics, and failure cases.
- [ ] No real secrets are committed.
- [ ] No unsupported production claims appear.
- [ ] Demo scope is honest and recruiter-friendly.

## Responsible Use

This template is for legitimate educational and portfolio demonstrations. It should not be used to create deceptive, malicious, privacy-invasive, credential-stealing, exploit-generating, surveillance, spam, or security-sensitive tooling.

## License

MIT
