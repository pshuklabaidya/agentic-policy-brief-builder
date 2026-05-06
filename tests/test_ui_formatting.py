from __future__ import annotations

import builtins
from dataclasses import dataclass
from pathlib import Path

import pytest

from agentic_policy_brief_builder.audit import (
    CitationAuditFinding,
    CitationAuditResult,
    CitationAuditSeverity,
)
from agentic_policy_brief_builder.drafting import BriefSection, EvidenceCitation, PolicyBriefDraft
from agentic_policy_brief_builder.ui import (
    citation_audit_to_markdown,
    policy_brief_to_markdown,
    policy_brief_to_pdf_bytes,
    policy_brief_to_text,
    retrieved_evidence_to_markdown,
)


@dataclass(frozen=True, slots=True)
class FakeRetrievalResult:
    evidence_id: str
    text: str
    rank: int = 1
    document_name: str = "Riverton Housing Packet.pdf"
    source_type: str = "pdf"
    page_number: int | None = 3
    chunk_index: int = 0


def test_policy_brief_markdown_includes_all_brief_sections() -> None:
    markdown = policy_brief_to_markdown(_draft())

    assert "# Policy Brief" in markdown
    assert "## Executive Summary" in markdown
    assert "## Key Findings" in markdown
    assert "## Policy Options" in markdown
    assert "## Risks and Tradeoffs" in markdown
    assert "## Recommendation" in markdown
    assert "## Evidence Used" in markdown


def test_markdown_helpers_include_evidence_ids() -> None:
    brief_markdown = policy_brief_to_markdown(_draft())
    evidence_markdown = retrieved_evidence_to_markdown(
        (FakeRetrievalResult(evidence_id="EVID-1", text="Evidence snippet"),)
    )

    assert "`EVID-1`" in brief_markdown
    assert "`EVID-2`" in brief_markdown
    assert "`EVID-1`" in evidence_markdown
    assert "Evidence snippet" in evidence_markdown


def test_citation_audit_markdown_includes_audit_findings() -> None:
    audit = CitationAuditResult(
        passed=False,
        findings=(
            CitationAuditFinding(
                severity=CitationAuditSeverity.ERROR,
                code="unknown_evidence_id",
                message="Cited evidence ID was not retrieved.",
                evidence_id="EVID-unknown",
            ),
        ),
        missing_citations=(),
        unknown_citations=("EVID-unknown",),
        unused_evidence_ids=("EVID-unused",),
        used_evidence_ids=("EVID-1",),
        available_evidence_ids=("EVID-1", "EVID-unused"),
    )

    markdown = citation_audit_to_markdown(audit)

    assert "**Result:** Failed" in markdown
    assert "unknown_evidence_id" in markdown
    assert "Cited evidence ID was not retrieved." in markdown
    assert "`EVID-unused`" in markdown


def test_empty_optional_fields_are_handled_cleanly() -> None:
    draft = object.__new__(PolicyBriefDraft)
    object.__setattr__(draft, "title", "Policy Brief")
    object.__setattr__(draft, "executive_summary", "Summary")
    object.__setattr__(draft, "key_findings", (_section("Finding", "EVID-1"),))
    object.__setattr__(draft, "policy_options", (_section("Option", "EVID-1"),))
    object.__setattr__(draft, "risks_and_tradeoffs", (_section("Risk", "EVID-1"),))
    object.__setattr__(draft, "recommendation", _section("Recommendation", "EVID-1"))
    object.__setattr__(draft, "evidence_used", ())
    audit = CitationAuditResult(
        passed=True,
        findings=(),
        missing_citations=(),
        unknown_citations=(),
        unused_evidence_ids=(),
        used_evidence_ids=("EVID-1",),
        available_evidence_ids=("EVID-1",),
    )

    brief_markdown = policy_brief_to_markdown(draft)
    audit_markdown = citation_audit_to_markdown(audit)
    evidence_markdown = retrieved_evidence_to_markdown(())

    assert "No cited evidence was recorded." in brief_markdown
    assert "No citation audit findings." in audit_markdown
    assert "### Unused Evidence IDs\nNone" in audit_markdown
    assert "No retrieved evidence." in evidence_markdown


def test_policy_brief_text_export_includes_title_evidence_ids_and_audit() -> None:
    audit = _audit()

    text = policy_brief_to_text(
        _draft(),
        (FakeRetrievalResult(evidence_id="EVID-1", text="Evidence snippet"),),
        audit,
    )

    assert "Policy Brief" in text
    assert "EVID-1" in text
    assert "EVID-2" in text
    assert "Citation Audit" in text
    assert "unused_retrieved_evidence" in text


def test_policy_brief_pdf_export_returns_pdf_bytes_without_repo_artifacts() -> None:
    before_pdf_files = set(Path.cwd().rglob("*.pdf"))

    pdf_bytes = policy_brief_to_pdf_bytes(
        _draft(),
        (FakeRetrievalResult(evidence_id="EVID-1", text="Evidence snippet"),),
        _audit(),
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert set(Path.cwd().rglob("*.pdf")) == before_pdf_files


def test_export_helpers_do_not_call_openai_apis(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def fail_openai_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "openai" or name.startswith("openai."):
            raise AssertionError("export helpers must not call OpenAI APIs")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_openai_import)

    draft = _draft()
    audit = _audit()

    assert policy_brief_to_markdown(draft).startswith("# Policy Brief")
    assert policy_brief_to_text(draft, (), audit).startswith("Policy Brief")
    assert policy_brief_to_pdf_bytes(draft, (), audit).startswith(b"%PDF-")


def _draft() -> PolicyBriefDraft:
    return PolicyBriefDraft(
        title="Policy Brief",
        executive_summary="Summary",
        key_findings=(
            BriefSection(
                heading="Finding",
                content="Finding content",
                evidence_ids=("EVID-1",),
            ),
        ),
        policy_options=(
            BriefSection(
                heading="Option",
                content="Option content",
                evidence_ids=("EVID-2",),
            ),
        ),
        risks_and_tradeoffs=(
            BriefSection(
                heading="Risk",
                content="Risk content",
                evidence_ids=("EVID-1",),
            ),
        ),
        recommendation=BriefSection(
            heading="Recommendation",
            content="Recommendation content",
            evidence_ids=("EVID-1", "EVID-2"),
        ),
        evidence_used=(
            EvidenceCitation(
                evidence_id="EVID-1",
                document_name="Riverton Housing Packet.pdf",
                source_type="pdf",
                page_number=3,
                chunk_index=0,
                cited_text="Evidence one",
            ),
            EvidenceCitation(
                evidence_id="EVID-2",
                document_name="Riverton Housing Packet.pdf",
                source_type="pdf",
                page_number=None,
                chunk_index=1,
                cited_text="Evidence two",
            ),
        ),
    )


def _audit() -> CitationAuditResult:
    return CitationAuditResult(
        passed=True,
        findings=(
            CitationAuditFinding(
                severity=CitationAuditSeverity.WARNING,
                code="unused_retrieved_evidence",
                message="Retrieved evidence ID was not cited in the draft.",
                evidence_id="EVID-unused",
            ),
        ),
        missing_citations=(),
        unknown_citations=(),
        unused_evidence_ids=("EVID-unused",),
        used_evidence_ids=("EVID-1", "EVID-2"),
        available_evidence_ids=("EVID-1", "EVID-2", "EVID-unused"),
    )


def _section(heading: str, evidence_id: str) -> BriefSection:
    return BriefSection(
        heading=heading,
        content=f"{heading} content",
        evidence_ids=(evidence_id,),
    )
