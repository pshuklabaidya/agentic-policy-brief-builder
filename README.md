# AI Project Template

Reusable Streamlit-first template for building AI portfolio projects focused on Agentic RAG, LLM evaluation, synthetic-data demos, AI automation, and decision-support workflows.

> Status: Template repository for AI portfolio projects. This repository is not a finished AI application.

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

## Synthetic-Data Disclosure Template

Use language like this in every generated project:

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
