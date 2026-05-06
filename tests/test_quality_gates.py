from __future__ import annotations

from dataclasses import dataclass, replace

from agentic_policy_brief_builder.audit import audit_policy_brief_citations
from agentic_policy_brief_builder.drafting import BriefSection, EvidenceCitation, PolicyBriefDraft
from agentic_policy_brief_builder.evals.fixtures import EvaluationFixture
from agentic_policy_brief_builder.evals.quality_gates import run_quality_gates


@dataclass(frozen=True, slots=True)
class FakeRetrievalResult:
    evidence_id: str = "EVID-1"
    text: str = "housing zoning transit affordability evidence"
    document_name: str = "packet.md"
    source_type: str = "synthetic"
    page_number: int | None = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 10
    distance: float = 0.1


def test_all_quality_gates_pass_for_valid_case() -> None:
    gates = _run_gates()

    assert all(gate.passed for gate in gates)
    assert tuple(gate.name for gate in gates) == (
        "retrieval_returns_evidence",
        "retrieval_matches_fixture_expectations",
        "brief_includes_required_sections",
        "brief_sections_are_nonempty",
        "key_findings_include_citations",
        "policy_options_include_citations",
        "risks_and_tradeoffs_include_citations",
        "recommendation_includes_citations",
        "citation_audit_passes",
        "markdown_export_includes_evidence_ids",
    )


def test_retrieval_nonempty_gate_fails_for_no_evidence() -> None:
    gates = _run_gates(retrieved_results=())

    assert _gate(gates, "retrieval_returns_evidence").passed is False


def test_retrieval_expectation_gate_fails_without_keywords_patterns_or_ids() -> None:
    gates = _run_gates(
        fixture=replace(
            _fixture(),
            expected_topic_keywords=("unmatched",),
            expected_evidence_ids=("EVID-missing",),
            expected_evidence_patterns=("not in evidence",),
        )
    )

    assert _gate(gates, "retrieval_matches_fixture_expectations").passed is False


def test_required_sections_gate_fails_when_expected_section_missing() -> None:
    gates = _run_gates(fixture=replace(_fixture(), expected_brief_sections=("appendix",)))

    assert _gate(gates, "brief_includes_required_sections").passed is False


def test_sections_nonempty_gate_fails_for_empty_group() -> None:
    draft = object.__new__(PolicyBriefDraft)
    good = _draft()
    object.__setattr__(draft, "title", good.title)
    object.__setattr__(draft, "executive_summary", good.executive_summary)
    object.__setattr__(draft, "key_findings", ())
    object.__setattr__(draft, "policy_options", good.policy_options)
    object.__setattr__(draft, "risks_and_tradeoffs", good.risks_and_tradeoffs)
    object.__setattr__(draft, "recommendation", good.recommendation)
    object.__setattr__(draft, "evidence_used", good.evidence_used)

    gates = _run_gates(draft=draft)

    assert _gate(gates, "brief_sections_are_nonempty").passed is False


def test_key_findings_citation_gate_fails_when_citations_missing() -> None:
    draft = replace(_draft(), key_findings=(_uncited_section("Finding"),))
    gates = _run_gates(draft=draft)

    assert _gate(gates, "key_findings_include_citations").passed is False
    assert _gate(gates, "citation_audit_passes").passed is False


def test_policy_options_citation_gate_fails_when_citations_missing() -> None:
    draft = replace(_draft(), policy_options=(_uncited_section("Option"),))
    gates = _run_gates(draft=draft)

    assert _gate(gates, "policy_options_include_citations").passed is False


def test_risks_citation_gate_fails_when_citations_missing() -> None:
    draft = replace(_draft(), risks_and_tradeoffs=(_uncited_section("Risk"),))
    gates = _run_gates(draft=draft)

    assert _gate(gates, "risks_and_tradeoffs_include_citations").passed is False


def test_recommendation_citation_gate_fails_when_citations_missing() -> None:
    draft = replace(_draft(), recommendation=_uncited_section("Recommendation"))
    gates = _run_gates(draft=draft)

    assert _gate(gates, "recommendation_includes_citations").passed is False


def test_markdown_evidence_id_gate_fails_when_export_omits_ids() -> None:
    gates = _run_gates(markdown="# Brief without evidence IDs\n")

    assert _gate(gates, "markdown_export_includes_evidence_ids").passed is False


def _run_gates(
    *,
    fixture: EvaluationFixture | None = None,
    retrieved_results: tuple[FakeRetrievalResult, ...] | tuple[()] = (FakeRetrievalResult(),),
    draft: PolicyBriefDraft | None = None,
    markdown: str | None = None,
):
    draft = _draft() if draft is None else draft
    audit = audit_policy_brief_citations(draft, retrieved_results or (FakeRetrievalResult(),))
    return run_quality_gates(
        fixture=_fixture() if fixture is None else fixture,
        retrieved_results=retrieved_results,
        draft=draft,
        citation_audit=audit,
        markdown=markdown,
    )


def _fixture() -> EvaluationFixture:
    return EvaluationFixture(
        case_id="case",
        question="What should Riverton do?",
        expected_topic_keywords=("housing", "zoning"),
        expected_evidence_ids=("EVID-1",),
        expected_evidence_patterns=("transit affordability",),
        expected_brief_sections=(
            "executive_summary",
            "key_findings",
            "policy_options",
            "risks_and_tradeoffs",
            "recommendation",
            "evidence_used",
        ),
    )


def _draft() -> PolicyBriefDraft:
    return PolicyBriefDraft(
        title="Brief",
        executive_summary="Summary",
        key_findings=(BriefSection("Finding", "Finding content", ("EVID-1",)),),
        policy_options=(BriefSection("Option", "Option content", ("EVID-1",)),),
        risks_and_tradeoffs=(BriefSection("Risk", "Risk content", ("EVID-1",)),),
        recommendation=BriefSection("Recommendation", "Recommendation content", ("EVID-1",)),
        evidence_used=(
            EvidenceCitation("EVID-1", "packet.md", "synthetic", None, 0, "Evidence text"),
        ),
    )


def _uncited_section(heading: str) -> BriefSection:
    section = object.__new__(BriefSection)
    object.__setattr__(section, "heading", heading)
    object.__setattr__(section, "content", f"{heading} content")
    object.__setattr__(section, "evidence_ids", ())
    return section


def _gate(gates, name: str):
    return next(gate for gate in gates if gate.name == name)
