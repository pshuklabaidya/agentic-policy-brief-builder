from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from agentic_policy_brief_builder.audit import (
    CitationAuditSeverity,
    audit_policy_brief_citations,
)
from agentic_policy_brief_builder.drafting import BriefSection, EvidenceCitation, PolicyBriefDraft


@dataclass(frozen=True, slots=True)
class FakeRetrievalResult:
    evidence_id: str
    text: str = "Evidence text"
    document_name: str = "Riverton Housing Packet.pdf"
    source_type: str = "pdf"
    page_number: int | None = 3
    chunk_index: int = 0


def test_passing_citation_audit() -> None:
    result = audit_policy_brief_citations(_draft(), _retrieval_results())

    assert result.passed is True
    assert result.findings == ()
    assert result.missing_citations == ()
    assert result.unknown_citations == ()
    assert result.unused_evidence_ids == ()
    assert result.used_evidence_ids == ("EVID-1", "EVID-2")
    assert result.available_evidence_ids == ("EVID-1", "EVID-2")


def test_unknown_evidence_ids_fail_the_audit() -> None:
    draft = replace(
        _draft(),
        recommendation=BriefSection(
            heading="Recommendation",
            content="Recommend an approach with invented evidence.",
            evidence_ids=("EVID-unknown",),
        ),
    )

    result = audit_policy_brief_citations(draft, _retrieval_results())

    assert result.passed is False
    assert result.unknown_citations == ("EVID-unknown",)
    assert _finding(result.findings, "unknown_evidence_id").severity is CitationAuditSeverity.ERROR


def test_missing_key_finding_citations_fail_the_audit() -> None:
    draft = replace(_draft(), key_findings=(_uncited_section("Finding"),))

    result = audit_policy_brief_citations(draft, _retrieval_results())

    assert result.passed is False
    assert result.missing_citations == ("key_findings[0]",)
    finding = _finding(result.findings, "missing_required_citation")
    assert finding.severity is CitationAuditSeverity.ERROR
    assert finding.section_name == "key_findings[0]"


def test_missing_policy_option_citations_fail_the_audit() -> None:
    draft = replace(_draft(), policy_options=(_uncited_section("Option"),))

    result = audit_policy_brief_citations(draft, _retrieval_results())

    assert result.passed is False
    assert result.missing_citations == ("policy_options[0]",)
    assert _finding(result.findings, "missing_required_citation").severity is (
        CitationAuditSeverity.ERROR
    )


def test_missing_risk_tradeoff_citations_fail_the_audit() -> None:
    draft = replace(_draft(), risks_and_tradeoffs=(_uncited_section("Risk"),))

    result = audit_policy_brief_citations(draft, _retrieval_results())

    assert result.passed is False
    assert result.missing_citations == ("risks_and_tradeoffs[0]",)
    assert _finding(result.findings, "missing_required_citation").severity is (
        CitationAuditSeverity.ERROR
    )


def test_missing_recommendation_citations_fail_the_audit() -> None:
    draft = replace(_draft(), recommendation=_uncited_section("Recommendation"))

    result = audit_policy_brief_citations(draft, _retrieval_results())

    assert result.passed is False
    assert result.missing_citations == ("recommendation",)
    assert _finding(result.findings, "missing_required_citation").severity is (
        CitationAuditSeverity.ERROR
    )


def test_unused_retrieved_evidence_is_reported_as_a_warning() -> None:
    result = audit_policy_brief_citations(
        _draft(),
        (*_retrieval_results(), FakeRetrievalResult(evidence_id="EVID-unused")),
    )

    assert result.passed is True
    assert result.unused_evidence_ids == ("EVID-unused",)
    warning = _finding(result.findings, "unused_retrieved_evidence")
    assert warning.severity is CitationAuditSeverity.WARNING
    assert warning.evidence_id == "EVID-unused"


def test_empty_retrieval_results_raise_a_clear_error() -> None:
    with pytest.raises(
        ValueError,
        match="retrieved_results must contain at least one result for citation audit",
    ):
        audit_policy_brief_citations(_draft(), ())


def test_audit_output_is_deterministic() -> None:
    draft = replace(
        _draft(),
        key_findings=(
            _uncited_section("Finding"),
            BriefSection(
                heading="Second finding",
                content="This finding cites unknown evidence.",
                evidence_ids=("EVID-unknown",),
            ),
        ),
    )
    retrieval_results = (*_retrieval_results(), FakeRetrievalResult(evidence_id="EVID-unused"))

    first = audit_policy_brief_citations(draft, retrieval_results)
    second = audit_policy_brief_citations(draft, retrieval_results)

    assert first == second
    assert tuple(finding.code for finding in first.findings) == (
        "missing_required_citation",
        "unknown_evidence_id",
        "unused_retrieved_evidence",
    )


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
                page_number=4,
                chunk_index=1,
                cited_text="Evidence two",
            ),
        ),
    )


def _retrieval_results() -> tuple[FakeRetrievalResult, ...]:
    return (
        FakeRetrievalResult(evidence_id="EVID-1", page_number=3, chunk_index=0),
        FakeRetrievalResult(evidence_id="EVID-2", page_number=4, chunk_index=1),
    )


def _uncited_section(heading: str) -> BriefSection:
    section = object.__new__(BriefSection)
    object.__setattr__(section, "heading", heading)
    object.__setattr__(section, "content", f"{heading} content")
    object.__setattr__(section, "evidence_ids", ())
    return section


def _finding(findings, code: str):
    return next(finding for finding in findings if finding.code == code)
