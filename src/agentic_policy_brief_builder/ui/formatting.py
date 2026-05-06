"""Markdown, text, and PDF formatting helpers for the Streamlit policy brief UI."""

from __future__ import annotations

import importlib.util
from collections.abc import Iterable
from io import BytesIO
from textwrap import wrap
from typing import Any

from agentic_policy_brief_builder.audit import CitationAuditFinding, CitationAuditResult
from agentic_policy_brief_builder.drafting import BriefSection, EvidenceCitation, PolicyBriefDraft

__all__ = [
    "citation_audit_to_markdown",
    "policy_brief_to_markdown",
    "policy_brief_to_pdf_bytes",
    "policy_brief_to_text",
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


def policy_brief_to_text(
    draft: PolicyBriefDraft,
    retrieved_results: Iterable[Any] = (),
    audit: CitationAuditResult | None = None,
) -> str:
    """Return a plain-text export for a citation-aware policy brief."""

    lines: list[str] = [
        draft.title.strip(),
        "",
        "Executive Summary",
        draft.executive_summary.strip(),
        "",
        "Key Findings",
        *_sections_to_text(draft.key_findings),
        "",
        "Policy Options",
        *_sections_to_text(draft.policy_options),
        "",
        "Risks and Tradeoffs",
        *_sections_to_text(draft.risks_and_tradeoffs),
        "",
        "Recommendation",
        *_section_to_text(draft.recommendation),
        "",
        "Evidence Used",
        *_evidence_used_to_text(draft.evidence_used),
    ]
    retrieved_text = retrieved_evidence_to_text(retrieved_results).strip()
    if retrieved_text:
        lines.extend(("", retrieved_text))
    if audit is not None:
        lines.extend(("", citation_audit_to_text(audit).strip()))
    return _clean_text(lines)


def policy_brief_to_pdf_bytes(
    draft: PolicyBriefDraft,
    retrieved_results: Iterable[Any] = (),
    audit: CitationAuditResult | None = None,
) -> bytes:
    """Return an in-memory PDF export for a citation-aware policy brief."""

    text_export = policy_brief_to_text(draft, retrieved_results, audit)
    if importlib.util.find_spec("reportlab") is None:
        return _simple_pdf_bytes(text_export, title=draft.title.strip())
    return _reportlab_pdf_bytes(text_export, title=draft.title.strip())


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


def citation_audit_to_text(audit: CitationAuditResult) -> str:
    """Return plain text summarizing citation-audit status and findings."""

    status = "Passed" if audit.passed else "Failed"
    lines: list[str] = [
        "Citation Audit",
        f"Result: {status}",
        "",
        "Findings",
        *_audit_findings_to_text(audit.findings),
        "",
        "Missing Citations",
        *_string_list_to_text(audit.missing_citations, empty_label="None"),
        "",
        "Unknown Citations",
        *_string_list_to_text(audit.unknown_citations, empty_label="None"),
        "",
        "Unused Evidence IDs",
        *_string_list_to_text(audit.unused_evidence_ids, empty_label="None"),
    ]
    return _clean_text(lines)


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


def retrieved_evidence_to_text(retrieved_results: Iterable[Any]) -> str:
    """Return plain text for ranked retrieved evidence snippets."""

    results = tuple(retrieved_results)
    lines: list[str] = ["Retrieved Evidence"]
    if not results:
        lines.extend(("", "No retrieved evidence."))
        return _clean_text(lines)

    for result in results:
        evidence_id = str(_read_attr(result, "evidence_id"))
        rank = _read_optional_attr(result, "rank")
        label = f"{rank}. {evidence_id}" if rank is not None else f"- {evidence_id}"
        lines.extend(
            (
                "",
                label,
                f"  Source: {_source_label(result)}",
                f"  Snippet: {_compact_snippet(str(_read_attr(result, 'text')))}",
            )
        )
    return _clean_text(lines)


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


def _sections_to_text(sections: Iterable[BriefSection]) -> list[str]:
    lines: list[str] = []
    for section in sections:
        lines.extend(_section_to_text(section))
    return lines or ["No sections generated."]


def _section_to_text(section: BriefSection) -> list[str]:
    evidence = ", ".join(section.evidence_ids)
    return [
        section.heading.strip(),
        section.content.strip(),
        f"Evidence IDs: {evidence if evidence else 'None'}",
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


def _evidence_used_to_text(evidence_used: Iterable[EvidenceCitation]) -> list[str]:
    citations = tuple(evidence_used)
    if not citations:
        return ["No cited evidence was recorded."]

    lines: list[str] = []
    for citation in citations:
        lines.extend(
            (
                f"- {citation.evidence_id} — {_citation_source_label(citation)}",
                f"  Cited text: {_compact_snippet(citation.cited_text)}",
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


def _audit_findings_to_text(findings: Iterable[CitationAuditFinding]) -> list[str]:
    finding_tuple = tuple(findings)
    if not finding_tuple:
        return ["No citation audit findings."]

    lines: list[str] = []
    for finding in finding_tuple:
        details = []
        if finding.section_name:
            details.append(f"section: {finding.section_name}")
        if finding.evidence_id:
            details.append(f"evidence: {finding.evidence_id}")
        suffix = f" ({'; '.join(details)})" if details else ""
        lines.append(
            f"- {finding.severity.value.upper()} {finding.code}: {finding.message}{suffix}"
        )
    return lines


def _string_list_to_markdown(values: Iterable[str], *, empty_label: str) -> list[str]:
    value_tuple = tuple(values)
    if not value_tuple:
        return [empty_label]
    return [f"- `{value}`" for value in value_tuple]


def _string_list_to_text(values: Iterable[str], *, empty_label: str) -> list[str]:
    value_tuple = tuple(values)
    if not value_tuple:
        return [empty_label]
    return [f"- {value}" for value in value_tuple]


def _reportlab_pdf_bytes(text_export: str, *, title: str) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(_pdf_escape(title), styles["Title"]), Spacer(1, 12)]
    for line in text_export.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
        elif not line.startswith((" ", "-")) and len(stripped) < 80:
            story.append(Paragraph(_pdf_escape(stripped), styles["Heading2"]))
        else:
            story.append(Paragraph(_pdf_escape(stripped), styles["BodyText"]))
    document.build(story)
    return buffer.getvalue()


def _simple_pdf_bytes(text_export: str, *, title: str) -> bytes:
    pages = _pdf_pages(text_export)
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids ["
        + b" ".join(f"{3 + index * 2} 0 R".encode("ascii") for index in range(len(pages)))
        + b"] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>",
    ]
    for index, page_lines in enumerate(pages):
        page_object = 3 + index * 2
        content_object = page_object + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
            f"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> >> >> "
            f"/Contents {content_object} 0 R >>".encode("ascii")
        )
        stream = _pdf_content_stream(page_lines, title=title if index == 0 else "")
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    output = BytesIO()
    output.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{object_number} 0 obj\n".encode("ascii"))
        output.write(body)
        output.write(b"\nendobj\n")
    xref_position = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_position}\n%%EOF\n".encode("ascii")
    )
    return output.getvalue()


def _pdf_pages(text_export: str) -> list[list[str]]:
    lines: list[str] = []
    for raw_line in text_export.splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(wrap(raw_line, width=88, subsequent_indent="  ") or [raw_line])
    lines_per_page = 48
    pages = [
        lines[index : index + lines_per_page]
        for index in range(0, len(lines), lines_per_page)
    ]
    return pages or [[""]]


def _pdf_content_stream(page_lines: list[str], *, title: str) -> bytes:
    commands: list[str] = ["BT"]
    y = 744
    if title:
        commands.append("/F2 18 Tf")
        commands.append(f"72 {y} Td ({_pdf_literal(title)}) Tj")
        y -= 28
        commands.append("/F1 10 Tf")
        commands.append(f"72 {y} Td")
    else:
        commands.append("/F1 10 Tf")
        commands.append(f"72 {y} Td")
    for index, line in enumerate(page_lines if not title else page_lines[1:]):
        if index:
            commands.append("0 -14 Td")
        commands.append(f"({_pdf_literal(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


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


def _pdf_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _pdf_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


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


def _clean_text(lines: Iterable[str]) -> str:
    return "\n".join(lines).strip() + "\n"
