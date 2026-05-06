"""Deterministic quality gates for local policy brief evaluations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from agentic_policy_brief_builder.audit import CitationAuditResult
from agentic_policy_brief_builder.drafting import BriefSection, PolicyBriefDraft
from agentic_policy_brief_builder.evals.fixtures import EvaluationFixture
from agentic_policy_brief_builder.ui.formatting import policy_brief_to_markdown

__all__ = ["QualityGateResult", "run_quality_gates"]


@dataclass(frozen=True, slots=True)
class QualityGateResult:
    """Pass/fail result for one deterministic quality gate."""

    name: str
    passed: bool
    message: str
    required: bool = True


def run_quality_gates(
    *,
    fixture: EvaluationFixture,
    retrieved_results: Iterable[Any],
    draft: PolicyBriefDraft,
    citation_audit: CitationAuditResult,
    markdown: str | None = None,
) -> tuple[QualityGateResult, ...]:
    """Run all local quality gates for one evaluation case in stable order."""

    retrieved_tuple = tuple(retrieved_results)
    markdown_export = policy_brief_to_markdown(draft) if markdown is None else markdown
    return (
        _gate_retrieval_nonempty(retrieved_tuple),
        _gate_retrieval_expectations(fixture, retrieved_tuple),
        _gate_required_sections(fixture, draft),
        _gate_sections_nonempty(draft),
        _gate_group_has_citations("key_findings_include_citations", draft.key_findings),
        _gate_group_has_citations("policy_options_include_citations", draft.policy_options),
        _gate_group_has_citations(
            "risks_and_tradeoffs_include_citations", draft.risks_and_tradeoffs
        ),
        _gate_section_has_citations("recommendation_includes_citations", draft.recommendation),
        _gate_citation_audit(citation_audit),
        _gate_markdown_includes_evidence_ids(markdown_export, draft),
    )


def _gate_retrieval_nonempty(retrieved_results: tuple[Any, ...]) -> QualityGateResult:
    count = len(retrieved_results)
    return QualityGateResult(
        name="retrieval_returns_evidence",
        passed=count > 0,
        message=f"Retrieved {count} evidence item(s).",
    )


def _gate_retrieval_expectations(
    fixture: EvaluationFixture, retrieved_results: tuple[Any, ...]
) -> QualityGateResult:
    evidence_text = _combined_evidence_text(retrieved_results)
    retrieved_ids = tuple(str(_read_attr(result, "evidence_id")) for result in retrieved_results)

    expected_id_matches = tuple(
        evidence_id for evidence_id in fixture.expected_evidence_ids if evidence_id in retrieved_ids
    )
    keyword_matches = tuple(
        keyword
        for keyword in fixture.expected_topic_keywords
        if keyword.lower() in evidence_text.lower()
    )
    pattern_matches = tuple(
        pattern
        for pattern in fixture.expected_evidence_patterns
        if pattern.lower() in evidence_text.lower()
    )

    passes_ids = bool(fixture.expected_evidence_ids) and bool(expected_id_matches)
    passes_keywords = len(keyword_matches) == len(fixture.expected_topic_keywords)
    passes_patterns = bool(fixture.expected_evidence_patterns) and bool(pattern_matches)
    passed = passes_ids or passes_keywords or passes_patterns
    return QualityGateResult(
        name="retrieval_matches_fixture_expectations",
        passed=passed,
        message=(
            f"Matched evidence IDs {expected_id_matches or 'none'}, "
            f"topic keywords {keyword_matches or 'none'}, "
            f"and evidence patterns {pattern_matches or 'none'}."
        ),
    )


def _gate_required_sections(
    fixture: EvaluationFixture, draft: PolicyBriefDraft
) -> QualityGateResult:
    available = _available_section_names(draft)
    missing = tuple(
        section_name
        for section_name in fixture.expected_brief_sections
        if section_name not in available
    )
    return QualityGateResult(
        name="brief_includes_required_sections",
        passed=not missing,
        message=(
            "All expected brief sections are present."
            if not missing
            else f"Missing expected brief section(s): {', '.join(missing)}."
        ),
    )


def _gate_sections_nonempty(draft: PolicyBriefDraft) -> QualityGateResult:
    empty = []
    if not draft.executive_summary.strip():
        empty.append("executive_summary")
    empty.extend(_empty_group_sections("key_findings", draft.key_findings))
    empty.extend(_empty_group_sections("policy_options", draft.policy_options))
    empty.extend(_empty_group_sections("risks_and_tradeoffs", draft.risks_and_tradeoffs))
    if not draft.recommendation.heading.strip() or not draft.recommendation.content.strip():
        empty.append("recommendation")
    return QualityGateResult(
        name="brief_sections_are_nonempty",
        passed=not empty,
        message="All brief sections are nonempty." if not empty else f"Empty: {', '.join(empty)}.",
    )


def _gate_group_has_citations(name: str, sections: Iterable[BriefSection]) -> QualityGateResult:
    section_tuple = tuple(sections)
    missing = tuple(
        str(index)
        for index, section in enumerate(section_tuple)
        if not _section_evidence_ids(section)
    )
    return QualityGateResult(
        name=name,
        passed=bool(section_tuple) and not missing,
        message=(
            "Every section in this group cites evidence."
            if section_tuple and not missing
            else f"Sections without citations: {', '.join(missing) if missing else 'all/none'}."
        ),
    )


def _gate_section_has_citations(name: str, section: BriefSection) -> QualityGateResult:
    evidence_ids = _section_evidence_ids(section)
    return QualityGateResult(
        name=name,
        passed=bool(evidence_ids),
        message=(
            f"Section cites evidence IDs: {', '.join(evidence_ids)}."
            if evidence_ids
            else "Section does not cite evidence IDs."
        ),
    )


def _gate_citation_audit(citation_audit: CitationAuditResult) -> QualityGateResult:
    return QualityGateResult(
        name="citation_audit_passes",
        passed=citation_audit.passed,
        message=(
            "Citation audit passed."
            if citation_audit.passed
            else f"Citation audit failed with {len(citation_audit.findings)} finding(s)."
        ),
    )


def _gate_markdown_includes_evidence_ids(
    markdown: str, draft: PolicyBriefDraft
) -> QualityGateResult:
    evidence_ids = _draft_evidence_ids(draft)
    missing = tuple(evidence_id for evidence_id in evidence_ids if evidence_id not in markdown)
    return QualityGateResult(
        name="markdown_export_includes_evidence_ids",
        passed=bool(evidence_ids) and not missing,
        message=(
            "Markdown export includes cited evidence IDs."
            if evidence_ids and not missing
            else (
                "Markdown missing evidence IDs: "
                f"{', '.join(missing) if missing else 'none cited'}."
            )
        ),
    )


def _available_section_names(draft: PolicyBriefDraft) -> frozenset[str]:
    section_names = {"title"}
    if draft.executive_summary.strip():
        section_names.add("executive_summary")
    if draft.key_findings:
        section_names.add("key_findings")
    if draft.policy_options:
        section_names.add("policy_options")
    if draft.risks_and_tradeoffs:
        section_names.add("risks_and_tradeoffs")
    if draft.recommendation:
        section_names.add("recommendation")
    if draft.evidence_used:
        section_names.add("evidence_used")
    return frozenset(section_names)


def _empty_group_sections(name: str, sections: Iterable[BriefSection]) -> tuple[str, ...]:
    section_tuple = tuple(sections)
    if not section_tuple:
        return (name,)
    return tuple(
        f"{name}[{index}]"
        for index, section in enumerate(section_tuple)
        if not section.heading.strip() or not section.content.strip()
    )


def _section_evidence_ids(section: BriefSection) -> tuple[str, ...]:
    return tuple(
        evidence_id
        for evidence_id in section.evidence_ids
        if isinstance(evidence_id, str) and evidence_id.strip()
    )


def _draft_evidence_ids(draft: PolicyBriefDraft) -> tuple[str, ...]:
    ordered: list[str] = []
    for section in (*draft.key_findings, *draft.policy_options, *draft.risks_and_tradeoffs):
        ordered.extend(_section_evidence_ids(section))
    ordered.extend(_section_evidence_ids(draft.recommendation))
    ordered.extend(citation.evidence_id for citation in draft.evidence_used)
    return _ordered_unique(ordered)


def _combined_evidence_text(retrieved_results: tuple[Any, ...]) -> str:
    return "\n".join(str(_read_attr(result, "text")) for result in retrieved_results)


def _read_attr(result: Any, name: str) -> Any:
    if isinstance(result, dict):
        return result[name]
    return getattr(result, name)


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)
