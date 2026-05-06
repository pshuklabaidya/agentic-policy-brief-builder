"""Citation-aware policy brief drafting workflow."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from typing import Any

from agentic_policy_brief_builder.config import AppConfig
from agentic_policy_brief_builder.drafting.schemas import (
    BriefSection,
    DraftingClient,
    DraftPolicyBriefRequest,
    EvidenceCitation,
    EvidenceContextItem,
    PolicyBriefDraft,
    policy_brief_draft_json_schema,
)

__all__ = [
    "DeterministicFakeDraftingClient",
    "OpenAIDraftingClient",
    "draft_policy_brief",
]

_MAX_CONTEXT_TEXT_CHARS = 1_200


@dataclass(frozen=True, slots=True)
class _RetrievedEvidence:
    evidence_id: str
    document_name: str
    source_type: str
    page_number: int | None
    chunk_index: int
    text: str


class OpenAIDraftingClient:
    """OpenAI-backed drafting client for structured policy brief generation."""

    def __init__(
        self,
        config: AppConfig,
        *,
        openai_client: Any | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or config.openai_model
        if openai_client is None:
            if not config.has_openai_api_key:
                msg = "OPENAI_API_KEY is required to create an OpenAI drafting client"
                raise ValueError(msg)
            from openai import OpenAI

            openai_client = OpenAI(api_key=config.openai_api_key)
        self._client = openai_client

    def draft_policy_brief(self, request: DraftPolicyBriefRequest) -> PolicyBriefDraft:
        """Draft a policy brief using OpenAI structured output when available."""

        prompt = _build_openai_prompt(request)
        if hasattr(self._client, "responses") and hasattr(self._client.responses, "create"):
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "policy_brief_draft",
                        "schema": policy_brief_draft_json_schema(),
                        "strict": True,
                    }
                },
            )
            return _parse_policy_brief_text(_response_output_text(response))

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "policy_brief_draft",
                    "schema": policy_brief_draft_json_schema(),
                    "strict": True,
                },
            },
        )
        return _parse_policy_brief_text(response.choices[0].message.content or "{}")


class DeterministicFakeDraftingClient:
    """Deterministic test drafting client that never calls external services."""

    def draft_policy_brief(self, request: DraftPolicyBriefRequest) -> PolicyBriefDraft:
        first = request.evidence_context[0]
        second = request.evidence_context[1] if len(request.evidence_context) > 1 else first
        citations = tuple(
            EvidenceCitation(
                evidence_id=item.evidence_id,
                document_name=item.document_name,
                source_type=item.source_type,
                page_number=item.page_number,
                chunk_index=item.chunk_index,
                cited_text=item.text,
            )
            for item in (first, second)
        )
        return PolicyBriefDraft(
            title=f"Policy Brief: {request.policy_question.strip()}",
            executive_summary="This deterministic draft summarizes retrieved evidence for testing.",
            key_findings=(
                BriefSection(
                    heading="Finding",
                    content=f"Retrieved evidence indicates: {first.text}",
                    evidence_ids=(first.evidence_id,),
                ),
            ),
            policy_options=(
                BriefSection(
                    heading="Option",
                    content="Use the cited evidence to design a focused policy option.",
                    evidence_ids=(second.evidence_id,),
                ),
            ),
            risks_and_tradeoffs=(
                BriefSection(
                    heading="Risk",
                    content=(
                        "Implementation tradeoffs should be monitored against "
                        "the cited evidence."
                    ),
                    evidence_ids=(first.evidence_id,),
                ),
            ),
            recommendation=BriefSection(
                heading="Recommendation",
                content="Proceed with a measured pilot and evaluate outcomes.",
                evidence_ids=(first.evidence_id, second.evidence_id),
            ),
            evidence_used=citations,
        )


def draft_policy_brief(
    policy_question: str,
    retrieved_results: Iterable[Any],
    *,
    drafting_client: DraftingClient | None = None,
    config: AppConfig | None = None,
) -> PolicyBriefDraft:
    """Generate a citation-aware policy brief from retrieved evidence results.

    The function validates input guardrails, builds compact drafting context,
    calls the provided drafting client, and rejects any generated citation that
    references an evidence ID outside the supplied retrieval results.
    """

    if not isinstance(policy_question, str):
        msg = "policy_question must be a string"
        raise TypeError(msg)
    normalized_question = policy_question.strip()
    if not normalized_question:
        msg = "policy_question must not be blank"
        raise ValueError(msg)

    evidence = tuple(_normalize_retrieved_evidence(retrieved_results))
    if not evidence:
        msg = "retrieved_results must contain at least one result"
        raise ValueError(msg)

    evidence_by_id = {item.evidence_id: item for item in evidence}
    request = DraftPolicyBriefRequest(
        policy_question=normalized_question,
        evidence_context=tuple(_context_item(item) for item in evidence),
    )
    client = drafting_client or OpenAIDraftingClient(config or AppConfig())
    draft = client.draft_policy_brief(request)

    cited_ids = _cited_evidence_ids(draft)
    unknown_ids = tuple(
        evidence_id for evidence_id in cited_ids if evidence_id not in evidence_by_id
    )
    if unknown_ids:
        unknown = ", ".join(unknown_ids)
        msg = f"Generated brief cites unknown evidence IDs: {unknown}"
        raise ValueError(msg)

    evidence_used_ids = _ordered_unique(
        (*cited_ids, *(item.evidence_id for item in draft.evidence_used))
    )
    refreshed_evidence_used = tuple(
        _citation_from_retrieved(evidence_by_id[evidence_id])
        for evidence_id in evidence_used_ids
    )
    return replace(draft, evidence_used=refreshed_evidence_used)


def _normalize_retrieved_evidence(
    retrieved_results: Iterable[Any],
) -> tuple[_RetrievedEvidence, ...]:
    normalized: list[_RetrievedEvidence] = []
    for index, result in enumerate(retrieved_results):
        text = _read_attr(result, "text", index)
        normalized.append(
            _RetrievedEvidence(
                evidence_id=str(_read_attr(result, "evidence_id", index)),
                document_name=str(_read_attr(result, "document_name", index)),
                source_type=str(_read_attr(result, "source_type", index)),
                page_number=_optional_int(_read_attr(result, "page_number", index)),
                chunk_index=int(_read_attr(result, "chunk_index", index)),
                text=str(text),
            )
        )
    return tuple(normalized)


def _read_attr(result: Any, name: str, index: int) -> Any:
    if isinstance(result, dict):
        if name in result:
            return result[name]
    elif hasattr(result, name):
        return getattr(result, name)
    msg = f"retrieved_results[{index}] is missing required field: {name}"
    raise ValueError(msg)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _context_item(item: _RetrievedEvidence) -> EvidenceContextItem:
    return EvidenceContextItem(
        evidence_id=item.evidence_id,
        document_name=item.document_name,
        source_type=item.source_type,
        page_number=item.page_number,
        chunk_index=item.chunk_index,
        text=_compact_text(item.text),
    )


def _compact_text(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= _MAX_CONTEXT_TEXT_CHARS:
        return compact
    return f"{compact[: _MAX_CONTEXT_TEXT_CHARS - 1]}…"


def _citation_from_retrieved(item: _RetrievedEvidence) -> EvidenceCitation:
    return EvidenceCitation(
        evidence_id=item.evidence_id,
        document_name=item.document_name,
        source_type=item.source_type,
        page_number=item.page_number,
        chunk_index=item.chunk_index,
        cited_text=_compact_text(item.text),
    )


def _cited_evidence_ids(draft: PolicyBriefDraft) -> tuple[str, ...]:
    ids: list[str] = []
    for section_group in (draft.key_findings, draft.policy_options, draft.risks_and_tradeoffs):
        for section in section_group:
            ids.extend(section.evidence_ids)
    ids.extend(draft.recommendation.evidence_ids)
    ids.extend(citation.evidence_id for citation in draft.evidence_used)
    return _ordered_unique(ids)


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _system_prompt() -> str:
    return (
        "You are a policy analyst drafting concise, evidence-grounded policy briefs. "
        "Use only evidence IDs supplied in the retrieval context. Every key finding, "
        "policy option, risk/tradeoff, and recommendation must include at least one "
        "supporting evidence_id. Do not invent evidence IDs."
    )


def _build_openai_prompt(request: DraftPolicyBriefRequest) -> str:
    evidence_lines = []
    for item in request.evidence_context:
        page = "none" if item.page_number is None else str(item.page_number)
        evidence_lines.append(
            "\n".join(
                (
                    f"Evidence ID: {item.evidence_id}",
                    f"Document: {item.document_name}",
                    f"Source type: {item.source_type}",
                    f"Page number: {page}",
                    f"Chunk index: {item.chunk_index}",
                    f"Text: {item.text}",
                )
            )
        )
    evidence_text = "\n\n".join(evidence_lines)
    return (
        f"Policy question: {request.policy_question}\n\n"
        "Retrieved evidence context:\n"
        f"{evidence_text}\n\n"
        "Draft a structured policy brief matching the requested schema. Include citation metadata "
        "in evidence_used for cited evidence."
    )


def _parse_policy_brief_text(text: str) -> PolicyBriefDraft:
    return PolicyBriefDraft.from_mapping(json.loads(text))


def _response_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = getattr(response, "output", None)
    if isinstance(output, Sequence):
        parts: list[str] = []
        for item in output:
            content = getattr(item, "content", None)
            if isinstance(content, Sequence):
                for content_item in content:
                    text = getattr(content_item, "text", None)
                    if isinstance(text, str):
                        parts.append(text)
        if parts:
            return "".join(parts)
    return "{}"
