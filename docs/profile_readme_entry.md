# GitHub Profile README Entry Draft

> Copy-ready entry for a GitHub profile README. Do not edit the separate profile repository as part of this project issue.

## Agentic Policy Brief Builder

**Agentic RAG Streamlit demo that turns local policy documents into cited policy brief drafts with retrieved evidence, citation audit, deterministic evals, and portfolio-ready quality gates.**

- Supports a safe synthetic Riverton policy packet plus local TXT/PDF upload workflows.
- Retrieves evidence chunks and generates structured sections for findings, options, risks/tradeoffs, recommendations, and evidence notes.
- Runs a citation audit to check whether cited evidence IDs map back to retrieved evidence.
- Exports the generated brief, evidence, and audit context as Markdown.

**Tech stack**

- Python, Streamlit, pytest, Ruff.
- Local Chroma vector retrieval and OpenAI-compatible embedding/drafting clients for the interactive workflow.
- Modular packages for ingestion, chunking, retrieval, drafting, citation audit, UI formatting, evals, and repository health.

**Validation and quality gates**

- Deterministic local evals with synthetic fixtures and fake clients.
- CI runs Ruff, pytest, local evals, repository-health checks, and release-readiness checks.
- Public docs cover limitations, release readiness, CI behavior, evaluation design, and demo boundaries.

**Demo note:** public demos use synthetic fictional data and are scoped as a portfolio artifact, not a production policy-analysis system.
