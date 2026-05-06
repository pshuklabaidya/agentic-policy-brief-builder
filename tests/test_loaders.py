from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from agentic_policy_brief_builder.ingestion.loaders import (
    DocumentRecord,
    load_document,
    load_documents,
    load_synthetic_policy_packet_records,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "documents"


def test_txt_fixture_loads_with_document_name_and_text() -> None:
    record = load_document(FIXTURES_DIR / "riverton_policy_note.txt")[0]

    assert record == DocumentRecord(
        document_name="riverton_policy_note.txt",
        source_type="txt",
        source_path=FIXTURES_DIR / "riverton_policy_note.txt",
        page_number=None,
        text=(
            "Riverton Housing Policy Note\n\n"
            "The city should pair zoning reform with tenant outreach and public reporting.\n"
        ),
    )


def test_batch_loader_reports_clear_non_fatal_errors() -> None:
    result = load_documents(
        [
            FIXTURES_DIR / "riverton_policy_note.txt",
            FIXTURES_DIR / "missing_policy.txt",
            FIXTURES_DIR / "unsupported.docx",
        ]
    )

    assert [record.document_name for record in result.records] == ["riverton_policy_note.txt"]
    assert len(result.errors) == 2
    assert result.errors[0].document_name == "missing_policy.txt"
    assert "Document does not exist" in result.errors[0].message
    assert result.errors[1].document_name == "unsupported.docx"
    assert "Unsupported document type '.docx'" in result.errors[1].message


@pytest.mark.skipif(importlib.util.find_spec("fitz") is None, reason="PyMuPDF is not installed")
def test_small_pdf_fixture_loads_page_numbers_and_text() -> None:
    records = load_document(FIXTURES_DIR / "small_policy_packet.pdf")

    assert [record.document_name for record in records] == ["small_policy_packet.pdf"]
    assert [record.source_type for record in records] == ["pdf"]
    assert [record.page_number for record in records] == [1]
    assert "Riverton PDF fixture policy text" in records[0].text


def test_pdf_loader_reports_dependency_error_without_failing_batch() -> None:
    if importlib.util.find_spec("fitz") is not None:
        pytest.skip("PyMuPDF is installed; PDF extraction is covered by the fixture test")

    result = load_documents([FIXTURES_DIR / "small_policy_packet.pdf"])

    assert result.records == ()
    assert len(result.errors) == 1
    assert result.errors[0].document_name == "small_policy_packet.pdf"
    assert "PDF loading requires PyMuPDF" in result.errors[0].message


def test_synthetic_packet_loader_is_preserved_as_normalized_records() -> None:
    records = load_synthetic_policy_packet_records()

    assert len(records) >= 3
    assert all(record.source_type == "synthetic" for record in records)
    assert all(record.document_name.endswith(".md") for record in records)
    assert all("Synthetic data notice:" in record.text for record in records)
