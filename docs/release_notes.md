# Release Notes

## First portfolio-ready release: `0.1.0`

This release establishes Agentic Policy Brief Builder as a public portfolio project: a Streamlit-based Agentic RAG demo that turns local policy documents into cited policy brief drafts with evidence review and citation auditing.

No GitHub release, tag, package publication, deployment, or hosted artifact is being created as part of this documentation issue.

## Major capabilities

- **Synthetic policy packet demo**: uses a fictional Riverton housing and zoning packet for safe public demos without private, employer, or confidential data.
- **Upload workflow**: accepts TXT and PDF policy documents for local document-grounded demos.
- **RAG pipeline**: ingests documents, chunks text, indexes evidence, retrieves relevant chunks, and drafts policy brief sections.
- **Citation-aware output**: includes cited key findings, options, risks/tradeoffs, recommendations, and a cited evidence appendix.
- **Citation audit**: checks whether cited evidence IDs in the draft correspond to retrieved evidence.
- **Markdown export**: formats the brief, retrieved evidence, and audit summary for download or review.

## Validation gates

The baseline includes deterministic, offline validation gates intended for repeatable portfolio review:

- `python -m ruff check .` for linting;
- `python -m pytest` for unit and regression tests;
- `python scripts/run_local_evals.py` for synthetic local evals;
- `python scripts/check_repo_health.py` for repository structure, generated-artifact, and secret-file checks;
- `python scripts/check_release_readiness.py` for public-readiness documentation and CI gate checks.

CI runs the same core gates without requiring a real `OPENAI_API_KEY` and without live OpenAI API calls.

## Limitations

- The project is a portfolio demo, not a production policy-analysis platform.
- Demo data is synthetic and does not prove performance on real municipal, legal, regulatory, or confidential documents.
- Deterministic local evals use fake clients and stable fixtures; they are regression checks, not broad model-quality evaluations.
- Production use would require human expert review, deeper evaluation, monitoring, access control, privacy controls, incident handling, and domain-specific governance.
