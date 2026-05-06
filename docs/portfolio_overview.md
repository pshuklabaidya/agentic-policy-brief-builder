# Portfolio Overview

## Business problem

Policy teams often need to turn long memos, public comments, timelines, and option papers into concise decision briefs. Manual synthesis is slow, citation tracking is error-prone, and unsupported summaries can create review risk.

## Product value

Agentic Policy Brief Builder demonstrates how an AI-assisted workflow can help analysts draft evidence-grounded policy briefs faster while keeping source citations visible. The project emphasizes reviewability over automation: it retrieves evidence, drafts structured sections, and audits whether citations point back to retrieved material.

## Target user

The demo is designed for policy analysts, civic technology teams, public-sector innovation groups, and AI product reviewers who want to evaluate document-grounded brief generation. It is also recruiter-friendly: the workflow, validation gates, and limitations are visible from the repository.

## Demo workflow

1. Choose the synthetic Riverton policy packet or upload TXT/PDF documents.
2. Enter a policy question.
3. Retrieve relevant evidence chunks.
4. Generate a structured policy brief draft with cited findings, options, risks, and recommendations.
5. Review retrieved evidence and citation-audit results.
6. Export the brief and audit context as Markdown.

Public demos should use the synthetic packet in `data/synthetic/policy_packet/`. The synthetic packet is fictional and is included only for educational and portfolio demonstration purposes.

## High-level architecture

```text
Streamlit UI
  -> document loader (synthetic packet or TXT/PDF upload)
  -> chunking pipeline
  -> local vector retrieval
  -> citation-aware drafting
  -> citation audit
  -> Markdown formatting/export
```

Supporting layers include typed schemas, deterministic local eval fixtures, pytest coverage, CI gates, repository-health checks, and release-readiness checks.

## Why citation audit matters

Citation audit makes the AI output easier to review. Instead of treating a draft as self-validating, the system checks whether cited evidence IDs in the generated sections map back to retrieved evidence. That does not prove every statement is correct, but it catches obvious citation drift and encourages reviewers to inspect source material before using a brief.

## Why deterministic evals and health checks matter

Deterministic evals and health checks make the project easier to trust as a portfolio artifact. They show that the ingestion, retrieval, drafting, citation-audit, and formatting paths can be tested without network calls, secrets, or live model availability. Repository-health and release-readiness checks also reduce accidental public-demo issues such as missing docs, local generated artifacts, or secret-bearing files.
