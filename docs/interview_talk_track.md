# Interview Talk Track

## Concise project summary

Agentic Policy Brief Builder is a Streamlit Agentic RAG portfolio project that turns synthetic or uploaded policy documents into cited policy brief drafts, then runs citation audit and deterministic local validation gates.

## 30-second version

I built a document-grounded policy brief builder for a public portfolio demo. It uses a synthetic municipal policy packet or uploaded TXT/PDF files, retrieves relevant evidence, drafts a structured policy brief with citations, and audits whether citations map back to retrieved evidence. I also added deterministic local evals, CI, repository-health checks, and release-readiness checks so the project is easy to review without secrets or live API calls.

## 2-minute version

The business problem is that policy teams often need to summarize long policy packets into decision-ready briefs, but manual synthesis is slow and citation tracking is easy to get wrong. This project demonstrates an AI-assisted workflow that keeps evidence visible.

The app is Streamlit-first. A user selects the synthetic Riverton policy packet or uploads TXT/PDF documents, asks a policy question, and the pipeline loads, chunks, retrieves, drafts, audits citations, and formats Markdown output. The synthetic dataset keeps the demo safe for public review.

The technical focus is not just generation; it is reviewability. The citation audit checks that evidence IDs cited in the draft correspond to retrieved evidence. Deterministic local evals use fake clients and fixtures to verify retrieval expectations, required brief sections, citation coverage, audit passing, and Markdown output. CI runs linting, tests, local evals, repo-health checks, and release-readiness checks without requiring an OpenAI API key.

I intentionally document the limitations: this is not production-ready, the evals are demo-scale, and real policy use would require expert review, access control, monitoring, stronger evaluation, and governance.

## Technical highlights

- Streamlit UX for synthetic-data and TXT/PDF upload workflows.
- Modular ingestion, chunking, retrieval, drafting, citation-audit, eval, and UI-formatting packages.
- Citation-aware drafting schema and audit path for source review.
- Deterministic local eval runner for offline regression checks.
- CI gates aligned with local developer commands.
- Repository-health and release-readiness scripts that check structure, docs, generated artifacts, secret-bearing files, and validation wiring.

## Likely interview questions and answer bullets

### Why did you use synthetic data?

- Public portfolio projects should avoid private, employer, customer, or confidential data.
- Synthetic data allows the workflow to be demonstrated safely and repeatedly.
- The README and docs disclose that demo results do not prove performance on real policy records.

### What makes this “agentic”?

- The app coordinates a multi-step workflow: load documents, chunk, retrieve evidence, draft a structured brief, audit citations, and format output.
- The emphasis is on an orchestrated evidence workflow rather than a single prompt.
- The project remains bounded: it does not autonomously publish, email, file, or act on policy recommendations.

### Why is citation audit important?

- It helps reviewers detect citation drift and unsupported references.
- It creates a review checkpoint between generated prose and source evidence.
- It is not a substitute for expert review, but it improves transparency.

### How do the evals work without live API calls?

- Local evals use deterministic fake clients and synthetic fixtures.
- They check stable behaviors such as retrieval expectations, required sections, citation coverage, audit status, and Markdown export.
- This keeps CI reliable and avoids needing secrets in public validation gates.

### What would you improve for production?

- Stronger evaluation against representative real-world corpora with expert labels.
- Authentication, authorization, tenant isolation, audit logging, and privacy controls.
- Monitoring for retrieval quality, model failures, latency, cost, and unsafe outputs.
- Human approval workflows and domain-specific governance.

## Tradeoffs and limitations

- Synthetic data improves demo safety but limits claims about real-world accuracy.
- Deterministic fake-client evals are stable but do not measure live model quality.
- Local retrieval is appropriate for a portfolio demo but would need scale, observability, and access controls in production.
- Citation audit checks evidence-ID grounding, not full factual correctness or policy validity.
- The app is a research aid, not legal, regulatory, lobbying, or financial advice.
