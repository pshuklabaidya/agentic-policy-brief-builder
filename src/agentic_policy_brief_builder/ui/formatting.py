"""Markdown formatting helpers for the Streamlit policy brief UI."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from agentic_policy_brief_builder.audit import CitationAuditFinding, CitationAuditResult
from agentic_policy_brief_builder.drafting import BriefSection, EvidenceCitation, PolicyBriefDraft

__all__ = [
    "citation_audit_to_markdown",
    "policy_brief_to_markdown",
    "retrieved_evidence_to_markdown",
]

_SNIPPET_MAX_CHARS = 700


def policy_brief_to_markdown(draft: PolicyBriefDraft) -> str:
    """Return a complete Markdown export for a citation-aware policy brief."""

    lines: list[str] = [
        f"# {draft.title.strip()}",
        "",
        "## Executive Summary",
        draft.executive_summary.strip(),
        "",
        "## Key Findings",
        *_sections_to_markdown(draft.key_findings),
        "",
        "## Policy Options",
        *_sections_to_markdown(draft.policy_options),
        "",
        "## Risks and Tradeoffs",
        *_sections_to_markdown(draft.risks_and_tradeoffs),
        "",
        "## Recommendation",
        *_section_to_markdown(draft.recommendation),
        "",
        "## Evidence Used",
        *_evidence_used_to_markdown(draft.evidence_used),
    ]
    return _clean_markdown(lines)


def citation_audit_to_markdown(audit: CitationAuditResult) -> str:
    """Return Markdown summarizing citation-audit status and findings."""

    status = "Passed" if audit.passed else "Failed"
    lines: list[str] = [
        "## Citation Audit",
        f"**Result:** {status}",
        "",
        "### Findings",
        *_audit_findings_to_markdown(audit.findings),
        "",
        "### Missing Citations",
        *_string_list_to_markdown(audit.missing_citations, empty_label="None"),
        "",
        "### Unknown Citations",
        *_string_list_to_markdown(audit.unknown_citations, empty_label="None"),
        "",
        "### Unused Evidence IDs",
        *_string_list_to_markdown(audit.unused_evidence_ids, empty_label="None"),
    ]
    return _clean_markdown(lines)


def retrieved_evidence_to_markdown(retrieved_results: Iterable[Any]) -> str:
    """Return Markdown for ranked retrieved evidence snippets."""

    results = tuple(retrieved_results)
    lines: list[str] = ["## Retrieved Evidence"]
    if not results:
        lines.extend(("", "No retrieved evidence."))
        return _clean_markdown(lines)

    for result in results:
        evidence_id = str(_read_attr(result, "evidence_id"))
        rank = _read_optional_attr(result, "rank")
        label = f"{rank}. `{evidence_id}`" if rank is not None else f"- `{evidence_id}`"
        lines.extend(
            (
                "",
                label,
                f"  - Source: {_source_label(result)}",
                f"  - Snippet: {_compact_snippet(str(_read_attr(result, 'text')))}",
            )
        )
    return _clean_markdown(lines)


def _sections_to_markdown(sections: Iterable[BriefSection]) -> list[str]:
    lines: list[str] = []
    for section in sections:
        lines.extend(_section_to_markdown(section))
    return lines or ["No sections generated."]


def _section_to_markdown(section: BriefSection) -> list[str]:
    evidence = ", ".join(f"`{evidence_id}`" for evidence_id in section.evidence_ids)
    return [
        f"### {section.heading.strip()}",
        section.content.strip(),
        f"**Evidence IDs:** {evidence if evidence else 'None'}",
        "",
    ]


def _evidence_used_to_markdown(evidence_used: Iterable[EvidenceCitation]) -> list[str]:
    citations = tuple(evidence_used)
    if not citations:
        return ["No cited evidence was recorded."]

    lines: list[str] = []
    for citation in citations:
        lines.extend(
            (
                f"- `{citation.evidence_id}` — {_citation_source_label(citation)}",
                f"  - Cited text: {_compact_snippet(citation.cited_text)}",
            )
        )
    return lines


def _audit_findings_to_markdown(findings: Iterable[CitationAuditFinding]) -> list[str]:
    finding_tuple = tuple(findings)
    if not finding_tuple:
        return ["No citation audit findings."]

    lines: list[str] = []
    for finding in finding_tuple:
        details = []
        if finding.section_name:
            details.append(f"section: `{finding.section_name}`")
        if finding.evidence_id:
            details.append(f"evidence: `{finding.evidence_id}`")
        suffix = f" ({'; '.join(details)})" if details else ""
        lines.append(
            f"- **{finding.severity.value.upper()}** `{finding.code}`: "
            f"{finding.message}{suffix}"
        )
    return lines


def _string_list_to_markdown(values: Iterable[str], *, empty_label: str) -> list[str]:
    value_tuple = tuple(values)
    if not value_tuple:
        return [empty_label]
    return [f"- `{value}`" for value in value_tuple]


def _source_label(result: Any) -> str:
    document_name = str(_read_attr(result, "document_name"))
    source_type = str(_read_attr(result, "source_type"))
    page_number = _read_optional_attr(result, "page_number")
    chunk_index = _read_optional_attr(result, "chunk_index")
    page = f", page {page_number}" if page_number is not None else ""
    chunk = f", chunk {chunk_index}" if chunk_index is not None else ""
    return f"{document_name} ({source_type}{page}{chunk})"


def _citation_source_label(citation: EvidenceCitation) -> str:
    page = f", page {citation.page_number}" if citation.page_number is not None else ""
    return f"{citation.document_name} ({citation.source_type}{page}, chunk {citation.chunk_index})"


def _compact_snippet(text: str, *, max_chars: int = _SNIPPET_MAX_CHARS) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 1].rstrip()}…"


def _read_attr(result: Any, name: str) -> Any:
    if isinstance(result, dict):
        return result[name]
    return getattr(result, name)


def _read_optional_attr(result: Any, name: str) -> Any | None:
    if isinstance(result, dict):
        return result.get(name)
    return getattr(result, name, None)


def _clean_markdown(lines: Iterable[str]) -> str:
    return "\n".join(lines).strip() + "\n"
