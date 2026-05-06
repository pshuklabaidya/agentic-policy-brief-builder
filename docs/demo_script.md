# Demo Script

Use the synthetic Riverton policy packet for public walkthroughs. It is fictional and safe for portfolio demonstration, but it does not prove performance on real policy records.

## 3-minute walkthrough

**0:00-0:30 — Frame the problem**

- “Policy teams often need to turn long document packets into concise decision briefs, but manual synthesis and citation tracking are slow.”
- “This project demonstrates an evidence-grounded Agentic RAG workflow for a public portfolio demo.”
- “The demo uses synthetic fictional data and is not a production policy-analysis system.”

**0:30-1:15 — Show the app flow**

- Open Streamlit with `python -m streamlit run app/streamlit_app.py`.
- Select `Use synthetic policy packet`.
- Enter: `Which zoning reform option best balances housing supply, affordability, displacement risk, and implementation feasibility?`
- Keep the default top-k value and generate the brief.

**1:15-2:10 — Explain evidence-grounded generation**

- Show the retrieved evidence expanders.
- Point out evidence IDs, document names, source type, page where available, chunk index, and text.
- Explain that the draft is generated from retrieved evidence and carries evidence IDs into sections.

**2:10-2:45 — Show audit and export**

- Show the citation audit result.
- Explain that audit checks cited IDs against retrieved evidence and reports missing or unused evidence.
- Download the Markdown brief to show portable review output.

**2:45-3:00 — Close with quality gates**

- Mention deterministic evals, pytest, Ruff, CI, repository-health checks, and release-readiness checks.
- Reiterate that real policy use would require expert review and production controls.

## 7-minute walkthrough

**0:00-1:00 — Product context**

- State the problem: long policy packets, tight review windows, fragile citation tracking.
- State the value: faster first-draft synthesis with visible evidence and audit checkpoints.
- Disclose synthetic data and demo scope.

**1:00-2:00 — Architecture overview**

- Walk through the pipeline: Streamlit UI → ingestion → chunking → local retrieval → drafting → citation audit → Markdown export.
- Mention modular packages for ingestion, retrieval, drafting, audit, UI formatting, evals, and health checks.

**2:00-3:00 — Synthetic packet workflow**

- Select `Use synthetic policy packet`.
- Ask a Riverton policy question.
- Generate the cited brief.
- Explain that this path is best for public demos because it avoids private or confidential data.

**3:00-4:00 — Upload workflow**

- Switch to `Upload TXT/PDF policy documents` to show the option, but avoid uploading sensitive files in a public demo.
- Explain that supported files are `.txt` and `.pdf` and loader warnings are surfaced in the UI.
- Return to synthetic data for the live generation path if needed.

**4:00-5:15 — Evidence-grounded generation**

- Open retrieved evidence results.
- Explain stable evidence IDs and how they connect source chunks to generated sections.
- Show key findings, policy options, risks/tradeoffs, recommendation, and evidence-used list.

**5:15-6:15 — Citation audit and quality gates**

- Show citation audit pass/fail status, findings, and unused evidence IDs.
- Clarify that the audit checks citation structure and retrieved-evidence grounding, not complete factual correctness.
- Mention deterministic local evals and CI gates that run without live API calls.

**6:15-7:00 — Limitations and next steps**

- Explain that production use would need expert-labeled evals, access control, privacy controls, monitoring, audit logging, cost controls, and governance.
- Position the project as a portfolio artifact for applied AI, RAG, and agentic workflow engineering.

## Talking points

### Evidence-grounded generation

- Retrieval happens before drafting, so the model receives a bounded evidence set.
- Evidence IDs are attached to chunks and reused in generated sections.
- Reviewers can inspect each retrieved chunk rather than relying on generated prose alone.

### Citation audit and quality gates

- Citation audit checks for missing required citations and citations to evidence IDs outside the retrieved set.
- Unused evidence IDs are reported as review signals, not necessarily errors.
- Local evals use synthetic fixtures and fake clients for deterministic CI-friendly checks.
- CI runs linting, tests, evals, repository-health checks, and release-readiness checks without requiring secrets.

## Likely demo questions and answers

**Q: Is this production-ready?**

A: No. It is a public portfolio demo and research aid. Production use would require stronger evaluation, security, privacy, monitoring, governance, and human review workflows.

**Q: Does citation audit prove the brief is correct?**

A: No. It verifies that cited evidence IDs map back to retrieved evidence and that required sections include citations. It does not prove every claim or recommendation is factually or legally correct.

**Q: Why synthetic data?**

A: Synthetic data keeps the public demo safe, reproducible, and free of private customer, employer, or confidential records.

**Q: Can it use real documents?**

A: The app supports local TXT/PDF uploads, but public demos should avoid confidential or regulated records. Real-world use would require appropriate data governance.

**Q: Do CI and evals call OpenAI?**

A: No. Tests, local evals, CI, repository-health checks, and release-readiness checks are deterministic and do not require live OpenAI API calls.
