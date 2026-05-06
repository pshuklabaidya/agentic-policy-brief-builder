# Roadmap

This roadmap keeps the project aligned with its current Streamlit, local RAG, deterministic-eval architecture. Items are candidates, not commitments.

## Near-term enhancements

- Add example screenshots or a short demo GIF using only the synthetic policy packet.
- Expand the synthetic packet with a second fictional policy domain to test topic transfer.
- Add more local eval fixtures for edge cases such as weak evidence, conflicting evidence, and missing citations.
- Improve README troubleshooting for common setup and dependency issues.
- Add lightweight architecture diagrams to complement the text overview.

## Medium-term enhancements

- Add optional reranking or hybrid lexical/vector retrieval while preserving offline test paths.
- Add a human-review checklist in the UI for citation inspection and policy-risk review.
- Add structured export formats such as JSON or DOCX templates for generated briefs.
- Track local eval history in a simple checked-in summary format, avoiding generated artifacts.
- Add broader tests for uploaded PDF/TXT handling and citation-audit failure modes.

## Long-term enhancements

- Introduce role-based access control, audit logging, and data-retention controls for a production-style reference architecture.
- Build a larger expert-labeled evaluation set with model-based and human-reviewed quality dimensions.
- Add observability for retrieval quality, model latency, cost, and error rates.
- Support multi-document comparison workflows for policy alternatives and stakeholder feedback themes.
- Package deployment guidance separately from the portfolio demo, with clear security and governance requirements.
