from __future__ import annotations

from math import dist
from pathlib import Path
from typing import Any

import pytest

from agentic_policy_brief_builder.config import AppConfig
from agentic_policy_brief_builder.ingestion.chunking import DocumentChunk
from agentic_policy_brief_builder.retrieval.vector_store import LocalChromaVectorStore


class DeterministicEmbeddingClient:
    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(_simple_embedding(text) for text in texts)


class FakeChromaClient:
    def __init__(self) -> None:
        self.collections: dict[str, FakeChromaCollection] = {}

    def get_or_create_collection(self, *, name: str) -> FakeChromaCollection:
        if name not in self.collections:
            self.collections[name] = FakeChromaCollection()
        return self.collections[name]


class FakeChromaCollection:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}

    def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        for row_id, embedding, document, metadata in zip(
            ids,
            embeddings,
            documents,
            metadatas,
            strict=True,
        ):
            self.rows[row_id] = {
                "embedding": embedding,
                "document": document,
                "metadata": metadata,
            }

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int,
        include: list[str],
    ) -> dict[str, Any]:
        del include
        query_embedding = query_embeddings[0]
        ranked_rows = sorted(
            self.rows.items(),
            key=lambda item: dist(query_embedding, item[1]["embedding"]),
        )[:n_results]
        return {
            "ids": [[row_id for row_id, _row in ranked_rows]],
            "documents": [[row["document"] for _row_id, row in ranked_rows]],
            "metadatas": [[row["metadata"] for _row_id, row in ranked_rows]],
            "distances": [
                [dist(query_embedding, row["embedding"]) for _row_id, row in ranked_rows]
            ],
        }


def test_vector_store_indexes_and_retrieves_ranked_chunks_with_evidence_ids(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    chunks = (
        _chunk(
            evidence_id="EVID-riverton-page-1-0",
            text="tenant protections and eviction diversion",
            page_number=1,
            chunk_index=0,
        ),
        _chunk(
            evidence_id="EVID-riverton-page-2-1",
            text="parking reform and minimums",
            page_number=2,
            chunk_index=1,
        ),
    )

    indexed_count = store.index_chunks(chunks)
    results = store.retrieve_relevant_chunks("tenant eviction", top_k=2)

    assert indexed_count == 2
    assert [result.rank for result in results] == [1, 2]
    assert results[0].evidence_id == "EVID-riverton-page-1-0"
    assert results[0].text == "tenant protections and eviction diversion"


def test_vector_store_preserves_document_metadata_after_retrieval(tmp_path: Path) -> None:
    store = _store(tmp_path)
    chunk = _chunk(
        evidence_id="EVID-housing-packet-page-7-3",
        document_name="Housing Packet.pdf",
        source_type="pdf",
        page_number=7,
        chunk_index=3,
        start_char=25,
        end_char=125,
        text="affordable housing trust fund",
    )

    store.index_chunks((chunk,))
    result = store.retrieve_relevant_chunks("housing trust", top_k=1)[0]

    assert result.document_name == "Housing Packet.pdf"
    assert result.source_type == "pdf"
    assert result.page_number == 7
    assert result.chunk_index == 3
    assert result.start_char == 25
    assert result.end_char == 125
    assert result.evidence_id == "EVID-housing-packet-page-7-3"


def test_vector_store_preserves_none_page_number_metadata(tmp_path: Path) -> None:
    store = _store(tmp_path)
    chunk = _chunk(
        evidence_id="EVID-policy-note-section-0",
        document_name="policy_note.txt",
        source_type="txt",
        page_number=None,
        text="local policy memo",
    )

    store.index_chunks((chunk,))
    result = store.retrieve_relevant_chunks("policy memo", top_k=1)[0]

    assert result.page_number is None
    assert result.document_name == "policy_note.txt"
    assert result.source_type == "txt"


def test_vector_store_rejects_blank_query(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="query must not be blank"):
        store.retrieve_relevant_chunks("   ")


def test_vector_store_rejects_empty_chunk_input(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="chunks must contain at least one"):
        store.index_chunks(())


def _store(tmp_path: Path) -> LocalChromaVectorStore:
    return LocalChromaVectorStore(
        AppConfig(openai_api_key="test-key", vector_store_dir=tmp_path),
        DeterministicEmbeddingClient(),
        chroma_client=FakeChromaClient(),
    )


def _chunk(
    *,
    evidence_id: str,
    text: str,
    document_name: str = "Riverton Packet.pdf",
    source_type: str = "pdf",
    page_number: int | None = 1,
    chunk_index: int = 0,
    start_char: int = 0,
    end_char: int | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        evidence_id=evidence_id,
        document_name=document_name,
        source_type=source_type,  # type: ignore[arg-type]
        page_number=page_number,
        chunk_index=chunk_index,
        text=text,
        start_char=start_char,
        end_char=len(text) if end_char is None else end_char,
    )


def _simple_embedding(text: str) -> tuple[float, float, float]:
    normalized = text.lower()
    return (
        float(normalized.count("tenant") + normalized.count("eviction")),
        float(normalized.count("parking")),
        float(len(normalized) / 100),
    )
