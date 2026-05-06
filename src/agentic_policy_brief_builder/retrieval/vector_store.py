"""Local Chroma vector storage and retrieval helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from agentic_policy_brief_builder.config import AppConfig
from agentic_policy_brief_builder.ingestion.chunking import DocumentChunk
from agentic_policy_brief_builder.retrieval.embeddings import (
    EmbeddingClient,
    validate_embedding_texts,
)

DEFAULT_COLLECTION_NAME = "policy_evidence_chunks"
_NONE_PAGE_NUMBER = ""

__all__ = [
    "DEFAULT_COLLECTION_NAME",
    "LocalChromaVectorStore",
    "RetrievalResult",
    "index_document_chunks",
    "retrieve_relevant_chunks",
]


class _ChromaCollection(Protocol):
    def upsert(
        self,
        *,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> Any: ...

    def query(
        self,
        *,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int,
        include: Sequence[str],
    ) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A ranked retrieval hit with citation-ready metadata."""

    rank: int
    evidence_id: str
    text: str
    document_name: str
    source_type: str
    page_number: int | None
    chunk_index: int
    start_char: int
    end_char: int
    distance: float


class LocalChromaVectorStore:
    """Persistent local Chroma store for policy evidence chunks."""

    def __init__(
        self,
        config: AppConfig,
        embedding_client: EmbeddingClient,
        *,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        chroma_client: Any | None = None,
    ) -> None:
        self.embedding_client = embedding_client
        self.collection_name = collection_name
        self.vector_store_dir = Path(config.vector_store_dir)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self._chroma_client = chroma_client or _create_persistent_chroma_client(
            self.vector_store_dir
        )
        self._collection = cast(
            _ChromaCollection,
            self._chroma_client.get_or_create_collection(name=collection_name),
        )

    def index_chunks(self, chunks: Iterable[DocumentChunk]) -> int:
        """Embed and upsert document chunks into the Chroma collection."""

        chunk_tuple = tuple(chunks)
        if not chunk_tuple:
            msg = "chunks must contain at least one DocumentChunk"
            raise ValueError(msg)

        texts = validate_embedding_texts(tuple(chunk.text for chunk in chunk_tuple))
        embeddings = self.embedding_client.embed_texts(texts)
        if len(embeddings) != len(chunk_tuple):
            msg = "embedding client returned a different number of embeddings than input texts"
            raise ValueError(msg)

        self._collection.upsert(
            ids=[chunk.evidence_id for chunk in chunk_tuple],
            embeddings=[list(embedding) for embedding in embeddings],
            documents=list(texts),
            metadatas=[_metadata_from_chunk(chunk) for chunk in chunk_tuple],
        )
        return len(chunk_tuple)

    def retrieve_relevant_chunks(
        self, query: str, *, top_k: int = 5
    ) -> tuple[RetrievalResult, ...]:
        """Embed a query and return ranked Chroma hits with citation metadata."""

        if not isinstance(query, str):
            msg = "query must be a string"
            raise TypeError(msg)
        if not query.strip():
            msg = "query must not be blank"
            raise ValueError(msg)
        if not isinstance(top_k, int) or isinstance(top_k, bool):
            msg = "top_k must be an integer"
            raise TypeError(msg)
        if top_k <= 0:
            msg = "top_k must be greater than 0"
            raise ValueError(msg)

        query_embedding = self.embedding_client.embed_texts((query,))[0]
        raw_results = self._collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return _results_from_chroma_query(raw_results)


def index_document_chunks(
    chunks: Iterable[DocumentChunk],
    *,
    config: AppConfig,
    embedding_client: EmbeddingClient,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> int:
    """Index chunks in the configured persistent local Chroma store."""

    store = LocalChromaVectorStore(
        config,
        embedding_client,
        collection_name=collection_name,
    )
    return store.index_chunks(chunks)


def retrieve_relevant_chunks(
    query: str,
    *,
    config: AppConfig,
    embedding_client: EmbeddingClient,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    top_k: int = 5,
) -> tuple[RetrievalResult, ...]:
    """Retrieve top-k relevant chunks from the configured local Chroma store."""

    store = LocalChromaVectorStore(
        config,
        embedding_client,
        collection_name=collection_name,
    )
    return store.retrieve_relevant_chunks(query, top_k=top_k)


def _create_persistent_chroma_client(vector_store_dir: Path) -> Any:
    from chromadb import PersistentClient

    return PersistentClient(path=str(vector_store_dir))


def _metadata_from_chunk(chunk: DocumentChunk) -> dict[str, Any]:
    return {
        "evidence_id": chunk.evidence_id,
        "document_name": chunk.document_name,
        "source_type": chunk.source_type,
        "page_number": chunk.page_number if chunk.page_number is not None else _NONE_PAGE_NUMBER,
        "chunk_index": chunk.chunk_index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
    }


def _results_from_chroma_query(raw_results: dict[str, Any]) -> tuple[RetrievalResult, ...]:
    ids = _first_result_list(raw_results, "ids")
    documents = _first_result_list(raw_results, "documents")
    metadatas = _first_result_list(raw_results, "metadatas")
    distances = _first_result_list(raw_results, "distances")

    results: list[RetrievalResult] = []
    for zero_based_rank, evidence_id in enumerate(ids):
        metadata = dict(metadatas[zero_based_rank] or {})
        text = documents[zero_based_rank]
        distance = distances[zero_based_rank]
        results.append(
            RetrievalResult(
                rank=zero_based_rank + 1,
                evidence_id=str(metadata.get("evidence_id") or evidence_id),
                text=str(text),
                document_name=str(metadata["document_name"]),
                source_type=str(metadata["source_type"]),
                page_number=_page_number_from_metadata(metadata.get("page_number")),
                chunk_index=int(metadata["chunk_index"]),
                start_char=int(metadata["start_char"]),
                end_char=int(metadata["end_char"]),
                distance=float(distance),
            )
        )
    return tuple(results)


def _first_result_list(raw_results: dict[str, Any], key: str) -> list[Any]:
    value = raw_results.get(key, [])
    if not value:
        return []
    first = value[0]
    return list(first) if first is not None else []


def _page_number_from_metadata(value: Any) -> int | None:
    if value in (None, _NONE_PAGE_NUMBER):
        return None
    return int(value)
