"""Retrieval-ready chunking for normalized policy document records."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from agentic_policy_brief_builder.ingestion.loaders import DocumentRecord, SourceType
from agentic_policy_brief_builder.retrieval.evidence import build_evidence_id

DEFAULT_CHUNK_SIZE = 1_000
DEFAULT_CHUNK_OVERLAP = 150

__all__ = [
    "ChunkSettings",
    "DocumentChunk",
    "chunk_document_record",
    "chunk_document_records",
    "validate_chunk_settings",
]


@dataclass(frozen=True, slots=True)
class ChunkSettings:
    """Configurable character-window chunking settings."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    def __post_init__(self) -> None:
        validate_chunk_settings(self.chunk_size, self.chunk_overlap)


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """A retrieval-ready text chunk with stable citation metadata."""

    evidence_id: str
    document_name: str
    source_type: SourceType
    page_number: int | None
    chunk_index: int
    text: str
    start_char: int
    end_char: int


def chunk_document_records(
    records: Iterable[DocumentRecord],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> tuple[DocumentChunk, ...]:
    """Chunk normalized document records for retrieval.

    Args:
        records: Normalized records from the ingestion loaders. PDF records are
            expected to be page-aware; TXT and synthetic records typically have
            no page number.
        chunk_size: Maximum number of characters in each chunk.
        chunk_overlap: Number of trailing characters repeated from one chunk in
            the next chunk for the same record.

    Returns:
        Retrieval-ready chunks with deterministic evidence IDs and source
        metadata. Empty or whitespace-only records are skipped.
    """

    settings = ChunkSettings(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[DocumentChunk] = []
    per_record_chunk_counts: dict[tuple[str, int | None], int] = {}

    for record in records:
        text = record.text
        if not text.strip():
            continue

        record_key = (record.document_name, record.page_number)
        chunk_index = per_record_chunk_counts.get(record_key, 0)
        for start_char, end_char, chunk_text in _iter_text_windows(
            text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ):
            chunks.append(
                DocumentChunk(
                    evidence_id=build_evidence_id(
                        record.document_name,
                        record.page_number,
                        chunk_index,
                    ),
                    document_name=record.document_name,
                    source_type=record.source_type,
                    page_number=record.page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    start_char=start_char,
                    end_char=end_char,
                )
            )
            chunk_index += 1
        per_record_chunk_counts[record_key] = chunk_index

    return tuple(chunks)


def chunk_document_record(
    record: DocumentRecord,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> tuple[DocumentChunk, ...]:
    """Chunk a single normalized document record."""

    return chunk_document_records(
        (record,),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def validate_chunk_settings(chunk_size: int, chunk_overlap: int) -> None:
    """Validate chunk settings and raise ``ValueError`` for invalid values."""

    if not _is_integer_candidate(chunk_size):
        msg = "chunk_size must be an integer"
        raise TypeError(msg)
    if not _is_integer_candidate(chunk_overlap):
        msg = "chunk_overlap must be an integer"
        raise TypeError(msg)
    if chunk_size <= 0:
        msg = "chunk_size must be greater than 0"
        raise ValueError(msg)
    if chunk_overlap < 0:
        msg = "chunk_overlap must be greater than or equal to 0"
        raise ValueError(msg)
    if chunk_overlap >= chunk_size:
        msg = "chunk_overlap must be smaller than chunk_size"
        raise ValueError(msg)


def _is_integer_candidate(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _iter_text_windows(
    text: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[tuple[int, int, str], ...]:
    windows: list[tuple[int, int, str]] = []
    step = chunk_size - chunk_overlap
    start_char = 0
    text_length = len(text)

    while start_char < text_length:
        end_char = min(start_char + chunk_size, text_length)
        windows.append((start_char, end_char, text[start_char:end_char]))
        if end_char == text_length:
            break
        start_char += step

    return tuple(windows)
