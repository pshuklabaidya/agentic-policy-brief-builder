# Local Evaluation Fixtures and Quality Gates

This project includes deterministic local evals for the synthetic Riverton policy packet. The evals are intended to catch regressions in the offline ingestion → chunking → retrieval → drafting → citation-audit → Markdown-export path.

## What the local evals check

The fixture file at `evals/fixtures/synthetic_policy_questions.json` contains ordered policy questions, expected topic keywords, expected evidence IDs or text patterns, and required brief sections. The local runner checks that:

- retrieval returns at least one evidence item;
- retrieved evidence matches fixture expectations through stable evidence IDs, topic keywords, or evidence text patterns;
- generated briefs include expected sections;
- generated brief sections are nonempty;
- key findings, policy options, risks/tradeoffs, and recommendations cite evidence IDs;
- the citation audit passes;
- Markdown export includes cited evidence IDs.

## Deterministic and offline by design

Local evals use only the synthetic policy packet under `data/synthetic/policy_packet`. They use deterministic fake clients and lexical local retrieval, so they do **not** make live OpenAI API calls and do **not** require `OPENAI_API_KEY`.

Hosted OpenAI Evals API integration, model-based graders, and generated PDF/DOCX reports are out of scope for this issue.

## Run local evals

From the repository root:

```bash
python scripts/run_local_evals.py
```

The script prints a concise pass/fail summary. It exits with code `0` when all required gates pass and exits with code `1` when any required gate fails.

To run a custom fixture file:

```bash
python scripts/run_local_evals.py --fixture-path path/to/fixtures.json
```
