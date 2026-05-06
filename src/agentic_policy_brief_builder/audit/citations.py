"""Deterministic citation audit checks for drafted policy briefs."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from agentic_policy_brief_builder.drafting import BriefSection, PolicyBriefDraft

__all__ = [
    "CitationAuditFinding",
    "CitationAuditResult",
    "CitationAuditSeverity",
    "audit_policy_brief_citations",
]


class CitationAuditSeverity(StrEnum):
    """Severity levels emitted by citation audit findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class CitationAuditFinding:
    """One deterministic citation audit finding."""

    severity: CitationAuditSeverity
    code: str
    message: str
    section_name: str | None = None
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.severity, CitationAuditSeverity):
            msg = "severity must be a CitationAuditSeverity"
            raise TypeError(msg)
        _require_nonblank_string("code", self.code)
        _require_nonblank_string("message", self.message)
        if self.section_name is not None:
            _require_nonblank_string("section_name", self.section_name)
        if self.evidence_id is not None:
            _require_nonblank_string("evidence_id", self.evidence_id)


@dataclass(frozen=True, slots=True)
class CitationAuditResult:
    """Summary of citation validity and retrieved-evidence coverage."""

    passed: bool
    findings: tuple[CitationAuditFinding, ...]
    missing_citations: tuple[str, ...]
    unknown_citations: tuple[str, ...]
    unused_evidence_ids: tuple[str, ...]
    used_evidence_ids: tuple[str, ...]
    available_evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            msg = "passed must be a boolean"
            raise TypeError(msg)
        object.__setattr__(self, "findings", tuple(self.findings))
        if not all(isinstance(finding, CitationAuditFinding) for finding in self.findings):
            msg = "findings must contain CitationAuditFinding entries"
            raise TypeError(msg)
        for field_name in (
            "missing_citations",
            "unknown_citations",
            "unused_evidence_ids",
            "used_evidence_ids",
            "available_evidence_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _string_tuple(field_name, getattr(self, field_name)),
            )


@dataclass(frozen=True, slots=True)
class _RequiredCitationSection:
    section_name: str
    section: BriefSection


def audit_policy_brief_citations(
    draft: PolicyBriefDraft,
    retrieved_results: Iterable[Any],
) -> CitationAuditResult:
    """Audit a policy brief draft for citation validity and evidence coverage.

    The audit is deterministic and purely local: it reads the supplied draft and
    retrieval results, verifies required-section citations, detects citations to
    evidence IDs outside the retrieval set, and reports retrieved evidence that
    was not cited by the draft. The supplied objects are not mutated.
    """

    if not isinstance(draft, PolicyBriefDraft):
        msg = "draft must be a PolicyBriefDraft"
        raise TypeError(msg)

    retrieved_tuple = tuple(retrieved_results)
    if not retrieved_tuple:
        msg = "retrieved_results must contain at least one result for citation audit"
        raise ValueError(msg)

    available_evidence_ids = _ordered_unique(
        str(_read_attr(result, "evidence_id", index))
        for index, result in enumerate(retrieved_tuple)
    )
    available_evidence_id_set = set(available_evidence_ids)

    required_sections = _required_citation_sections(draft)
    section_cited_evidence_ids = _ordered_unique(
        evidence_id
        for required_section in required_sections
        for evidence_id in _section_evidence_ids(required_section.section)
    )
    evidence_used_ids = _ordered_unique(citation.evidence_id for citation in draft.evidence_used)
    citation_reference_ids = _ordered_unique((*section_cited_evidence_ids, *evidence_used_ids))

    missing_citations = tuple(
        required_section.section_name
        for required_section in required_sections
        if not _section_evidence_ids(required_section.section)
    )
    unknown_citations = tuple(
        evidence_id
        for evidence_id in citation_reference_ids
        if evidence_id not in available_evidence_id_set
    )
    used_evidence_id_set = set(section_cited_evidence_ids)
    unused_evidence_ids = tuple(
        evidence_id
        for evidence_id in available_evidence_ids
        if evidence_id not in used_evidence_id_set
    )

    findings = _build_findings(
        missing_citations=missing_citations,
        unknown_citations=unknown_citations,
        unused_evidence_ids=unused_evidence_ids,
    )
    passed = not any(finding.severity is CitationAuditSeverity.ERROR for finding in findings)

    return CitationAuditResult(
        passed=passed,
        findings=findings,
        missing_citations=missing_citations,
        unknown_citations=unknown_citations,
        unused_evidence_ids=unused_evidence_ids,
        used_evidence_ids=section_cited_evidence_ids,
        available_evidence_ids=available_evidence_ids,
    )


def _required_citation_sections(draft: PolicyBriefDraft) -> tuple[_RequiredCitationSection, ...]:
    sections: list[_RequiredCitationSection] = []
    sections.extend(
        _RequiredCitationSection(f"key_findings[{index}]", section)
        for index, section in enumerate(draft.key_findings)
    )
    sections.extend(
        _RequiredCitationSection(f"policy_options[{index}]", section)
        for index, section in enumerate(draft.policy_options)
    )
    sections.extend(
        _RequiredCitationSection(f"risks_and_tradeoffs[{index}]", section)
        for index, section in enumerate(draft.risks_and_tradeoffs)
    )
    sections.append(_RequiredCitationSection("recommendation", draft.recommendation))
    return tuple(sections)


def _section_evidence_ids(section: BriefSection) -> tuple[str, ...]:
    return tuple(
        evidence_id
        for evidence_id in section.evidence_ids
        if isinstance(evidence_id, str) and evidence_id.strip()
    )


def _build_findings(
    *,
    missing_citations: tuple[str, ...],
    unknown_citations: tuple[str, ...],
    unused_evidence_ids: tuple[str, ...],
) -> tuple[CitationAuditFinding, ...]:
    findings: list[CitationAuditFinding] = []
    findings.extend(
        CitationAuditFinding(
            severity=CitationAuditSeverity.ERROR,
            code="missing_required_citation",
            message=f"Required section lacks cited evidence IDs: {section_name}",
            section_name=section_name,
        )
        for section_name in missing_citations
    )
    findings.extend(
        CitationAuditFinding(
            severity=CitationAuditSeverity.ERROR,
            code="unknown_evidence_id",
            message=f"Cited evidence ID was not present in retrieved evidence: {evidence_id}",
            evidence_id=evidence_id,
        )
        for evidence_id in unknown_citations
    )
    findings.extend(
        CitationAuditFinding(
            severity=CitationAuditSeverity.WARNING,
            code="unused_retrieved_evidence",
            message=f"Retrieved evidence ID was not cited in the draft: {evidence_id}",
            evidence_id=evidence_id,
        )
        for evidence_id in unused_evidence_ids
    )
    return tuple(findings)


def _read_attr(result: Any, name: str, index: int) -> Any:
    if isinstance(result, dict):
        if name in result:
            return result[name]
    elif hasattr(result, name):
        return getattr(result, name)
    msg = f"retrieved_results[{index}] is missing required field: {name}"
    raise ValueError(msg)


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _string_tuple(field_name: str, values: Sequence[str]) -> tuple[str, ...]:
    value_tuple = tuple(values)
    for index, value in enumerate(value_tuple):
        if not isinstance(value, str):
            msg = f"{field_name}[{index}] must be a string"
            raise TypeError(msg)
    return value_tuple


def _require_nonblank_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if not value.strip():
        msg = f"{field_name} must not be blank"
        raise ValueError(msg)
