"""Deterministic local evaluation runner."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from agentic_policy_brief_builder.audit import CitationAuditResult, audit_policy_brief_citations
from agentic_policy_brief_builder.drafting import (
    DeterministicFakeDraftingClient,
    DraftingClient,
    PolicyBriefDraft,
    draft_policy_brief,
)
from agentic_policy_brief_builder.evals.fixtures import (
    DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH,
    EvaluationFixture,
    load_evaluation_fixtures,
)
from agentic_policy_brief_builder.evals.quality_gates import QualityGateResult, run_quality_gates
from agentic_policy_brief_builder.ingestion.chunking import DocumentChunk, chunk_document_records
from agentic_policy_brief_builder.ingestion.loaders import load_synthetic_policy_packet_records
from agentic_policy_brief_builder.retrieval.embeddings import validate_embedding_texts
from agentic_policy_brief_builder.retrieval.vector_store import RetrievalResult
from agentic_policy_brief_builder.ui.formatting import policy_brief_to_markdown

__all__ = [
    "DeterministicFakeEmbeddingClient",
    "EvaluationCaseResult",
    "EvaluationRunResult",
    "run_local_evaluation",
]

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True, slots=True)
class EvaluationCaseResult:
    """Structured result for one evaluation fixture case."""

    fixture: EvaluationFixture
    retrieved_results: tuple[RetrievalResult, ...]
    draft: PolicyBriefDraft
    citation_audit: CitationAuditResult
    markdown: str
    quality_gates: tuple[QualityGateResult, ...]

    @property
    def passed(self) -> bool:
        """Whether all required gates passed for this case."""

        return all(gate.passed for gate in self.quality_gates if gate.required)


@dataclass(frozen=True, slots=True)
class EvaluationRunResult:
    """Structured result for a deterministic local evaluation run."""

    fixture_path: Path
    case_results: tuple[EvaluationCaseResult, ...]

    @property
    def passed(self) -> bool:
        """Whether all evaluation cases passed all required gates."""

        return all(case_result.passed for case_result in self.case_results)

    @property
    def total_cases(self) -> int:
        """Number of evaluated fixtures."""

        return len(self.case_results)

    @property
    def failed_cases(self) -> tuple[EvaluationCaseResult, ...]:
        """Evaluation cases with at least one required gate failure."""

        return tuple(case_result for case_result in self.case_results if not case_result.passed)


class DeterministicFakeEmbeddingClient:
    """Small deterministic embedding fake that never calls external services."""

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        validated_texts = validate_embedding_texts(texts)
        return tuple(_lexical_embedding(text) for text in validated_texts)


def run_local_evaluation(
    fixture_path: str | Path = DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH,
    *,
    drafting_client: DraftingClient | None = None,
    top_k: int = 4,
    chunk_size: int = 900,
    chunk_overlap: int = 100,
) -> EvaluationRunResult:
    """Run deterministic local evals against the synthetic policy packet."""

    resolved_fixture_path = Path(fixture_path)
    fixtures = load_evaluation_fixtures(resolved_fixture_path)
    records = load_synthetic_policy_packet_records()
    chunks = chunk_document_records(
        records,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    fake_drafting_client = drafting_client or DeterministicFakeDraftingClient()

    case_results: list[EvaluationCaseResult] = []
    for fixture in fixtures:
        retrieved_results = _retrieve_relevant_chunks(fixture.question, chunks, top_k=top_k)
        draft = draft_policy_brief(
            fixture.question,
            retrieved_results,
            drafting_client=fake_drafting_client,
        )
        citation_audit = audit_policy_brief_citations(draft, retrieved_results)
        markdown = policy_brief_to_markdown(draft)
        gates = run_quality_gates(
            fixture=fixture,
            retrieved_results=retrieved_results,
            draft=draft,
            citation_audit=citation_audit,
            markdown=markdown,
        )
        case_results.append(
            EvaluationCaseResult(
                fixture=fixture,
                retrieved_results=retrieved_results,
                draft=draft,
                citation_audit=citation_audit,
                markdown=markdown,
                quality_gates=gates,
            )
        )

    return EvaluationRunResult(
        fixture_path=resolved_fixture_path,
        case_results=tuple(case_results),
    )


def _retrieve_relevant_chunks(
    query: str,
    chunks: Iterable[DocumentChunk],
    *,
    top_k: int,
) -> tuple[RetrievalResult, ...]:
    if top_k <= 0:
        msg = "top_k must be greater than 0"
        raise ValueError(msg)
    query_vector = _lexical_embedding(query)
    query_tokens = set(_tokens(query))
    scored = sorted(
        ((_score_chunk(query_vector, query_tokens, chunk), chunk) for chunk in chunks),
        key=lambda item: (-item[0], item[1].document_name, item[1].chunk_index),
    )[:top_k]
    return tuple(
        RetrievalResult(
            rank=index + 1,
            evidence_id=chunk.evidence_id,
            text=chunk.text,
            document_name=chunk.document_name,
            source_type=chunk.source_type,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            distance=1.0 / (score + 1.0),
        )
        for index, (score, chunk) in enumerate(scored)
    )


def _score_chunk(
    query_vector: tuple[float, ...], query_tokens: set[str], chunk: DocumentChunk
) -> float:
    chunk_tokens = set(_tokens(chunk.text))
    overlap_score = len(query_tokens & chunk_tokens) * 10.0
    cosine_score = _cosine_similarity(query_vector, _lexical_embedding(chunk.text))
    return overlap_score + cosine_score


def _lexical_embedding(text: str) -> tuple[float, ...]:
    normalized = text.lower()
    terms = (
        "housing",
        "zoning",
        "transit",
        "affordability",
        "displacement",
        "accessible",
        "community",
        "monitoring",
        "timeline",
        "metrics",
        "permits",
        "rents",
        "parking",
        "adu",
        "tenant",
    )
    return tuple(float(normalized.count(term)) for term in terms)


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.lower()))
