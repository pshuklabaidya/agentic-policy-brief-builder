# Demo Walkthrough

This walkthrough describes the end-to-end Streamlit demo for Agentic Policy Brief Builder. It is intended for public portfolio review and should be presented as a bounded demo, not as a production policy-analysis system.

## Synthetic-data disclosure

Use the included synthetic Riverton policy packet for public demos whenever possible. The packet in `data/synthetic/policy_packet/` is fictional and was created for safe portfolio demonstration and deterministic evaluation. It does not include private customer data, employer data, confidential records, production exports, or real policy case files, and it does not prove performance on real policy documents.

## Run locally

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python -m streamlit run app/streamlit_app.py
```

The interactive app requires local configuration for model-backed embedding and drafting. Deterministic tests, local evals, CI gates, repository-health checks, and release-readiness checks do not require a real `OPENAI_API_KEY`.

## End-to-end Streamlit flow

1. **Open the app.** Confirm the page title is `Agentic Policy Brief Builder` and the configuration status is visible.
2. **Select a document source.** Choose either `Use synthetic policy packet` or `Upload TXT/PDF policy documents`.
3. **Enter a policy question.** Ask a question that can be answered from the selected documents, such as: `What are the main tradeoffs in the proposed zoning reform package?`
4. **Choose top-k evidence.** Keep the default for a concise demo or raise it to show more retrieved context.
5. **Generate the cited policy brief.** Click `Generate cited policy brief` and watch the status panel report loading, chunking, indexing, retrieval, drafting, and citation audit progress.
6. **Review retrieved evidence.** Expand the ranked evidence results and point out each evidence ID, document name, source type, page when available, chunk index, and text excerpt.
7. **Review the generated brief.** Walk through the executive summary, key findings, policy options, risks/tradeoffs, recommendation, and evidence-used list.
8. **Review citation audit.** Show whether the audit passed, any findings, and unused evidence IDs. Explain that this is a grounding check against retrieved evidence IDs, not a full factual or legal review.
9. **Download Markdown.** Use `Download Markdown brief` to export the generated brief, retrieved evidence, and citation-audit context for offline review.

## Synthetic packet path

For the safest public demo path:

1. Select `Use synthetic policy packet`.
2. Use a Riverton-specific question, for example: `Which zoning reform option best balances housing supply, affordability, displacement risk, and implementation feasibility?`
3. Emphasize that the workflow demonstrates evidence visibility and citation review on fictional data.

## TXT/PDF upload path

For a custom local demo:

1. Select `Upload TXT/PDF policy documents`.
2. Upload one or more `.txt` or `.pdf` files.
3. Ask a question grounded in those files.
4. Review loader warnings if any document cannot be parsed.
5. Do not upload confidential, private, employer, customer, or regulated documents in a public demo.

## What to say during the demo

- The app is designed to make evidence visible, not to replace expert policy analysis.
- Evidence IDs connect generated sections back to retrieved chunks.
- Citation audit catches missing section citations and citations to evidence IDs that were not retrieved.
- Local evals and CI gates are deterministic and synthetic-data-based, so reviewers can validate the project without secrets or live model calls.
- Production use would require stronger evaluation, access control, privacy controls, monitoring, governance, and human approval workflows.
