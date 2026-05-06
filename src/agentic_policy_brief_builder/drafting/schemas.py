"""Typed schemas for citation-aware policy brief drafting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "BriefSection",
    "DraftPolicyBriefRequest",
    "DraftingClient",
    "EvidenceCitation",
    "EvidenceContextItem",
    "PolicyBriefDraft",
    "policy_brief_draft_json_schema",
]


@dataclass(frozen=True, slots=True)
class EvidenceCitation:
    """Citation metadata preserved from a retrieved evidence chunk."""

    evidence_id: str
    document_name: str
    source_type: str
    page_number: int | None
    chunk_index: int
    cited_text: str

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "document_name", "source_type", "cited_text"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                msg = f"{field_name} must be a string"
                raise TypeError(msg)
            if not value.strip():
                msg = f"{field_name} must not be blank"
                raise ValueError(msg)
        if self.page_number is not None and not _is_int(self.page_number):
            msg = "page_number must be an integer or None"
            raise TypeError(msg)
        if not _is_int(self.chunk_index):
            msg = "chunk_index must be an integer"
            raise TypeError(msg)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> EvidenceCitation:
        return cls(
            evidence_id=str(data["evidence_id"]),
            document_name=str(data["document_name"]),
            source_type=str(data["source_type"]),
            page_number=_optional_int(data.get("page_number")),
            chunk_index=int(data["chunk_index"]),
            cited_text=str(data["cited_text"]),
        )


@dataclass(frozen=True, slots=True)
class BriefSection:
    """One citation-backed section or bullet in a policy brief."""

    heading: str
    content: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonblank_string("heading", self.heading)
        _require_nonblank_string("content", self.content)
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        if not self.evidence_ids:
            msg = "brief section evidence_ids must contain at least one evidence ID"
            raise ValueError(msg)
        blank_positions = [
            str(index)
            for index, evidence_id in enumerate(self.evidence_ids)
            if not isinstance(evidence_id, str) or not evidence_id.strip()
        ]
        if blank_positions:
            positions = ", ".join(blank_positions)
            msg = (
                "brief section evidence_ids must not contain blank values "
                f"at positions: {positions}"
            )
            raise ValueError(msg)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> BriefSection:
        return cls(
            heading=str(data["heading"]),
            content=str(data["content"]),
            evidence_ids=tuple(str(value) for value in data["evidence_ids"]),
        )


@dataclass(frozen=True, slots=True)
class PolicyBriefDraft:
    """A citation-aware policy brief draft."""

    title: str
    executive_summary: str
    key_findings: tuple[BriefSection, ...]
    policy_options: tuple[BriefSection, ...]
    risks_and_tradeoffs: tuple[BriefSection, ...]
    recommendation: BriefSection
    evidence_used: tuple[EvidenceCitation, ...]

    def __post_init__(self) -> None:
        _require_nonblank_string("title", self.title)
        _require_nonblank_string("executive_summary", self.executive_summary)
        object.__setattr__(self, "key_findings", _section_tuple(self.key_findings))
        object.__setattr__(self, "policy_options", _section_tuple(self.policy_options))
        object.__setattr__(
            self,
            "risks_and_tradeoffs",
            _section_tuple(self.risks_and_tradeoffs),
        )
        if not isinstance(self.recommendation, BriefSection):
            msg = "recommendation must be a BriefSection"
            raise TypeError(msg)
        object.__setattr__(self, "evidence_used", tuple(self.evidence_used))
        if not all(isinstance(citation, EvidenceCitation) for citation in self.evidence_used):
            msg = "evidence_used must contain EvidenceCitation entries"
            raise TypeError(msg)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> PolicyBriefDraft:
        return cls(
            title=str(data["title"]),
            executive_summary=str(data["executive_summary"]),
            key_findings=tuple(BriefSection.from_mapping(item) for item in data["key_findings"]),
            policy_options=tuple(
                BriefSection.from_mapping(item) for item in data["policy_options"]
            ),
            risks_and_tradeoffs=tuple(
                BriefSection.from_mapping(item) for item in data["risks_and_tradeoffs"]
            ),
            recommendation=BriefSection.from_mapping(data["recommendation"]),
            evidence_used=tuple(
                EvidenceCitation.from_mapping(item) for item in data.get("evidence_used", ())
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceContextItem:
    """Compact evidence context passed to a drafting client."""

    evidence_id: str
    document_name: str
    source_type: str
    page_number: int | None
    chunk_index: int
    text: str


@dataclass(frozen=True, slots=True)
class DraftPolicyBriefRequest:
    """Boundary object for policy brief drafting clients."""

    policy_question: str
    evidence_context: tuple[EvidenceContextItem, ...]

    def __post_init__(self) -> None:
        _require_nonblank_string("policy_question", self.policy_question)
        object.__setattr__(self, "evidence_context", tuple(self.evidence_context))
        if not self.evidence_context:
            msg = "evidence_context must contain at least one evidence item"
            raise ValueError(msg)


class DraftingClient(Protocol):
    """Interface for policy brief drafting clients."""

    def draft_policy_brief(self, request: DraftPolicyBriefRequest) -> PolicyBriefDraft:
        """Return a citation-aware policy brief draft for the supplied request."""


def policy_brief_draft_json_schema() -> dict[str, Any]:
    """Return the JSON schema used for OpenAI structured-output requests."""

    evidence_citation = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "evidence_id": {"type": "string"},
            "document_name": {"type": "string"},
            "source_type": {"type": "string"},
            "page_number": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "chunk_index": {"type": "integer"},
            "cited_text": {"type": "string"},
        },
        "required": [
            "evidence_id",
            "document_name",
            "source_type",
            "page_number",
            "chunk_index",
            "cited_text",
        ],
    }
    brief_section = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "heading": {"type": "string"},
            "content": {"type": "string"},
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
        },
        "required": ["heading", "content", "evidence_ids"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "executive_summary": {"type": "string"},
            "key_findings": {"type": "array", "items": brief_section, "minItems": 1},
            "policy_options": {"type": "array", "items": brief_section, "minItems": 1},
            "risks_and_tradeoffs": {
                "type": "array",
                "items": brief_section,
                "minItems": 1,
            },
            "recommendation": brief_section,
            "evidence_used": {"type": "array", "items": evidence_citation},
        },
        "required": [
            "title",
            "executive_summary",
            "key_findings",
            "policy_options",
            "risks_and_tradeoffs",
            "recommendation",
            "evidence_used",
        ],
    }


def _section_tuple(sections: tuple[BriefSection, ...]) -> tuple[BriefSection, ...]:
    section_tuple = tuple(sections)
    if not section_tuple:
        msg = "brief section groups must contain at least one section"
        raise ValueError(msg)
    if not all(isinstance(section, BriefSection) for section in section_tuple):
        msg = "brief section groups must contain BriefSection entries"
        raise TypeError(msg)
    return section_tuple


def _require_nonblank_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if not value.strip():
        msg = f"{field_name} must not be blank"
        raise ValueError(msg)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
