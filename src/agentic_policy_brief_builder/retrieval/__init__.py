"""Retrieval helpers for policy brief generation."""

from typing import Any

from agentic_policy_brief_builder.retrieval.embeddings import (
    EmbeddingClient,
    OpenAIEmbeddingClient,
    validate_embedding_texts,
)
from agentic_policy_brief_builder.retrieval.evidence import (
    build_evidence_id,
    document_slug,
    evidence_page_or_section,
)

__all__ = [
    "DEFAULT_COLLECTION_NAME",
    "EmbeddingClient",
    "LocalChromaVectorStore",
    "OpenAIEmbeddingClient",
    "RetrievalResult",
    "build_evidence_id",
    "document_slug",
    "evidence_page_or_section",
    "index_document_chunks",
    "retrieve_relevant_chunks",
    "validate_embedding_texts",
]

_VECTOR_STORE_EXPORTS = {
    "DEFAULT_COLLECTION_NAME",
    "LocalChromaVectorStore",
    "RetrievalResult",
    "index_document_chunks",
    "retrieve_relevant_chunks",
}


def __getattr__(name: str) -> Any:
    if name in _VECTOR_STORE_EXPORTS:
        from agentic_policy_brief_builder.retrieval import vector_store

        return getattr(vector_store, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
