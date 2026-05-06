from __future__ import annotations

import pytest

from agentic_policy_brief_builder.ingestion.chunking import (
    ChunkSettings,
    chunk_document_record,
    chunk_document_records,
)
from agentic_policy_brief_builder.ingestion.loaders import DocumentRecord
from agentic_policy_brief_builder.retrieval.evidence import build_evidence_id, document_slug


def test_evidence_ids_are_deterministic() -> None:
    record = DocumentRecord(
        document_name="Riverton Policy Note.txt",
        source_type="txt",
        text="abcdefghi",
    )

    first = chunk_document_record(record, chunk_size=4, chunk_overlap=1)
    second = chunk_document_record(record, chunk_size=4, chunk_overlap=1)

    assert [chunk.evidence_id for chunk in first] == [chunk.evidence_id for chunk in second]
    assert [chunk.evidence_id for chunk in first] == [
        "EVID-riverton-policy-note-section-0",
        "EVID-riverton-policy-note-section-1",
        "EVID-riverton-policy-note-section-2",
    ]


def test_txt_derived_document_chunks_include_required_metadata() -> None:
    record = DocumentRecord(
        document_name="riverton_policy_note.txt",
        source_type="txt",
        page_number=None,
        text="Riverton should pair zoning reform with tenant outreach.",
    )

    chunks = chunk_document_record(record, chunk_size=20, chunk_overlap=5)

    assert chunks[0].evidence_id == "EVID-riverton-policy-note-section-0"
    assert chunks[0].document_name == "riverton_policy_note.txt"
    assert chunks[0].source_type == "txt"
    assert chunks[0].page_number is None
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "Riverton should pair"
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 20


def test_pdf_page_derived_document_chunks_use_page_in_evidence_id() -> None:
    records = (
        DocumentRecord(
            document_name="Small Policy Packet.pdf",
            source_type="pdf",
            page_number=1,
            text="Page one policy evidence for zoning.",
        ),
        DocumentRecord(
            document_name="Small Policy Packet.pdf",
            source_type="pdf",
            page_number=2,
            text="Page two policy evidence for implementation.",
        ),
    )

    chunks = chunk_document_records(records, chunk_size=100, chunk_overlap=0)

    assert [chunk.evidence_id for chunk in chunks] == [
        "EVID-small-policy-packet-page-1-0",
        "EVID-small-policy-packet-page-2-0",
    ]
    assert [chunk.text for chunk in chunks] == [record.text for record in records]


def test_chunk_overlap_behavior_uses_configurable_character_windows() -> None:
    record = DocumentRecord(document_name="overlap.txt", source_type="txt", text="abcdefghij")

    chunks = chunk_document_record(record, chunk_size=4, chunk_overlap=2)

    assert [chunk.text for chunk in chunks] == ["abcd", "cdef", "efgh", "ghij"]
    assert [(chunk.start_char, chunk.end_char) for chunk in chunks] == [
        (0, 4),
        (2, 6),
        (4, 8),
        (6, 10),
    ]


def test_page_number_is_preserved_on_pdf_chunks() -> None:
    record = DocumentRecord(
        document_name="housing_packet.pdf",
        source_type="pdf",
        page_number=7,
        text="abcdefghi",
    )

    chunks = chunk_document_record(record, chunk_size=4, chunk_overlap=0)

    assert [chunk.page_number for chunk in chunks] == [7, 7, 7]
    assert [chunk.evidence_id for chunk in chunks] == [
        "EVID-housing-packet-page-7-0",
        "EVID-housing-packet-page-7-1",
        "EVID-housing-packet-page-7-2",
    ]


def test_human_readable_slug_generation() -> None:
    assert document_slug("2026 Housing & Zoning Options (Final).pdf") == (
        "2026-housing-zoning-options-final"
    )
    assert document_slug(r"C:\\Packets\\Riverton_Policy_Note.TXT") == "riverton-policy-note"
    assert build_evidence_id("Riverton_Policy_Note.TXT", None, 3) == (
        "EVID-riverton-policy-note-section-3"
    )


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap", "error_type", "message"),
    [
        (0, 0, ValueError, "chunk_size must be greater than 0"),
        (10, -1, ValueError, "chunk_overlap must be greater than or equal to 0"),
        (10, 10, ValueError, "chunk_overlap must be smaller than chunk_size"),
        (10, 11, ValueError, "chunk_overlap must be smaller than chunk_size"),
        (10.5, 1, TypeError, "chunk_size must be an integer"),
        (10, 1.5, TypeError, "chunk_overlap must be an integer"),
    ],
)
def test_invalid_chunk_settings_raise_clear_errors(
    chunk_size: int,
    chunk_overlap: int,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        ChunkSettings(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
