# Technical Deep Dive

Agentic Policy Brief Builder is a Streamlit Agentic RAG demo for producing reviewable, cited policy brief drafts from local documents. The technical goal is not autonomous policy decision-making; it is an inspectable workflow that retrieves evidence, drafts from that evidence, audits citations, and exports review context.

## Architecture

```text
Streamlit UI
  -> document source selection
  -> ingestion loaders
  -> chunking and evidence-ID assignment
  -> local vector indexing and retrieval
  -> citation-aware drafting
  -> deterministic citation audit
  -> Markdown formatting and download
```

The source code is organized into focused packages under `src/agentic_policy_brief_builder/`:

- `ingestion`: synthetic packet, TXT, and PDF loading plus chunking.
- `retrieval`: evidence-ID utilities, embedding client integration, and local Chroma vector store.
- `drafting`: structured brief schemas and citation-aware generation.
- `audit`: deterministic citation checks.
- `ui`: Markdown formatting helpers.
- `evals`: deterministic local evaluation fixtures and gates.
- `health`: repository-health and release-readiness checks.

## Ingestion and chunking

The app starts with either the synthetic Riverton policy packet or uploaded TXT/PDF documents. Loaders normalize files into document records with document name, source type, text, and page number when available. The chunking layer splits non-empty records into retrieval-ready text windows with configurable chunk size and overlap.

Chunk metadata is intentionally citation-friendly: each chunk keeps its document name, source type, optional page number, chunk index, character span, text, and evidence ID. This makes downstream retrieval results easier for reviewers to inspect.

## Evidence IDs

Evidence IDs are deterministic labels assigned to chunks. They follow the pattern:

```text
EVID-{document_slug}-{page_or_section}-{chunk_index}
```

Examples include `EVID-riverton-housing-memo-section-0` for a text or synthetic section and `EVID-policy-report-page-2-0` for a PDF page chunk. These IDs are short enough to cite in generated prose while still pointing reviewers back to retrieved material.

## Local retrieval

For the interactive app, chunks are indexed into a local Chroma collection through an embedding client. A user question is embedded, compared against indexed chunks, and returned as ranked retrieval results. Each result includes rank, evidence ID, document metadata, score/distance metadata where available, and text.

The project keeps retrieval local to the app workflow. It does not add hosted deployment, managed vector databases, or production data pipelines.

## Citation-aware drafting

Drafting receives the policy question and retrieved evidence results, then produces a structured policy brief draft. The draft includes an executive summary, key findings, policy options, risks/tradeoffs, a recommendation, and an evidence-used list. Evidence IDs are carried into the generated sections so reviewers can connect claims back to retrieved chunks.

The drafting workflow is designed for reviewability. It is not a guarantee that every sentence is complete, correct, or policy-sound; expert review remains required for real policy work.

## Citation audit

The citation audit is deterministic and local. It checks whether required draft sections include evidence IDs and whether cited evidence IDs were present in the retrieved evidence set. It also reports retrieved evidence that was not cited by the draft.

This catches common grounding issues, such as missing citations or references to unavailable evidence. It does not verify every factual claim, legal interpretation, budget estimate, or policy recommendation.

## Deterministic evals

The local eval runner uses synthetic fixtures and fake clients to test the workflow without network calls or real API keys. The evals are designed to catch regressions in expected retrieval behavior, required brief structure, citation coverage, audit status, and Markdown formatting.

These evals are intentionally demo-scale. They support portfolio review and CI stability, but they are not a substitute for expert-labeled evaluation on representative real-world corpora.

## CI and release-readiness checks

The GitHub Actions CI workflow mirrors local validation commands: Ruff linting, pytest, deterministic local evals, repository-health checks, and release-readiness checks. These gates do not require `OPENAI_API_KEY` and do not make live OpenAI API calls.

Repository-health checks verify expected files, package directories, scripts, tests, synthetic data, and basic secret/artifact hygiene. Release-readiness checks verify public-facing documentation, synthetic-data disclosure, validation guidance, CI wiring, and required portfolio docs.

## Portfolio scope

This project is intentionally bounded as a public portfolio artifact. Production use would require stronger data governance, authentication, authorization, privacy controls, observability, cost controls, live-model evaluation, expert review workflows, and operational monitoring.
