# Limitations

## Demo scope

Agentic Policy Brief Builder is a public portfolio demonstration of an Agentic RAG policy brief workflow. It is intended to show product thinking, architecture, testing discipline, citation review, and responsible documentation.

It is not a production policy-analysis platform and should not be used as the sole basis for legal, regulatory, lobbying, financial, budgetary, or public-policy decisions.

## Production scope would be larger

Real production use would require capabilities that are intentionally outside this demo, including:

- expert human review and approval workflows;
- representative real-world evaluation datasets and domain-specific graders;
- monitoring for retrieval quality, model quality, latency, cost, and failures;
- authentication, authorization, access control, and tenant isolation;
- privacy, retention, redaction, and data-governance controls;
- audit logging, incident response, and change-management practices;
- model-risk, legal, accessibility, security, and policy-domain review.

## Synthetic-data usage

The included Riverton policy packet is synthetic. It is fictional and exists so the app can be demonstrated publicly without private customer data, employer data, confidential records, or production exports.

Synthetic data is useful for safe demos and repeatable tests, but it does not prove performance on real municipal records, legal documents, public comments, or sensitive policy files.

## Deterministic local evals

Local evals use deterministic fake clients and stable synthetic fixtures. They are designed to catch regressions in ingestion, retrieval, brief structure, citation coverage, citation audit, and Markdown formatting without requiring live OpenAI API calls or secrets.

These evals are not a comprehensive quality benchmark. They do not measure broad factual accuracy, policy soundness, expert preference, safety across adversarial inputs, or performance on diverse real-world corpora.

## Citation-audit boundaries

Citation audit checks whether cited evidence IDs in the generated brief correspond to retrieved evidence. It does not prove that every sentence is fully supported, that the retrieved evidence is complete, or that the recommended policy option is correct.

Reviewers should inspect the source evidence and apply domain expertise before relying on any generated brief.
