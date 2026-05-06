"""Document loaders for policy-source ingestion.

The loaders in this module normalize supported source files into small,
page-aware records that later retrieval and citation steps can consume. Batch
loading is intentionally tolerant: a bad file becomes a structured loader error
instead of stopping ingestion for the rest of the policy packet.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentic_policy_brief_builder.ingestion.synthetic_packet import load_synthetic_policy_packet

SourceType = Literal["txt", "pdf", "synthetic"]
SUPPORTED_DOCUMENT_SUFFIXES = frozenset({".pdf", ".txt"})


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    """Normalized text extracted from a source policy document."""

    document_name: str
    source_type: SourceType
    text: str
    page_number: int | None = None
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class LoaderError:
    """Non-fatal document loading error captured during batch ingestion."""

    document_name: str
    source_type: str
    message: str
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class DocumentLoadResult:
    """Documents and non-fatal errors produced by a loader call."""

    records: tuple[DocumentRecord, ...]
    errors: tuple[LoaderError, ...] = ()


def load_documents(paths: Iterable[str | Path]) -> DocumentLoadResult:
    """Load supported TXT and PDF files from paths without failing the batch.

    Args:
        paths: Files or directories to ingest. Directories are scanned in sorted
            filename order for first-level supported files only.

    Returns:
        A normalized load result. Unsupported, missing, unreadable, or malformed
        inputs are reported as ``LoaderError`` instances and do not prevent other
        files from loading.
    """

    records: list[DocumentRecord] = []
    errors: list[LoaderError] = []

    for candidate in _iter_document_paths(paths):
        try:
            records.extend(load_document(candidate))
        except Exception as exc:  # noqa: BLE001 - batch loading must stay non-fatal.
            errors.append(_loader_error_from_exception(candidate, exc))

    return DocumentLoadResult(records=tuple(records), errors=tuple(errors))


def load_document(path: str | Path) -> tuple[DocumentRecord, ...]:
    """Load one TXT or PDF file into normalized document records.

    This function raises clear exceptions for invalid inputs. Use
    ``load_documents`` when callers need non-fatal batch behavior.
    """

    source_path = Path(path)
    if not source_path.exists():
        msg = f"Document does not exist: {source_path}"
        raise FileNotFoundError(msg)
    if not source_path.is_file():
        msg = f"Document path is not a file: {source_path}"
        raise ValueError(msg)

    suffix = source_path.suffix.lower()
    if suffix == ".txt":
        return (load_txt_document(source_path),)
    if suffix == ".pdf":
        return load_pdf_document(source_path)

    supported = ", ".join(sorted(SUPPORTED_DOCUMENT_SUFFIXES))
    msg = (
        f"Unsupported document type '{suffix or '<none>'}' for {source_path}. "
        f"Supported: {supported}."
    )
    raise ValueError(msg)


def load_txt_document(path: str | Path) -> DocumentRecord:
    """Load a UTF-8 TXT policy document."""

    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        msg = f"TXT document is not valid UTF-8: {source_path}"
        raise ValueError(msg) from exc

    return DocumentRecord(
        document_name=source_path.name,
        source_type="txt",
        source_path=source_path,
        page_number=None,
        text=text,
    )


def load_pdf_document(path: str | Path) -> tuple[DocumentRecord, ...]:
    """Load a PDF policy document into one record per page.

    Page numbers are 1-indexed so citations match how policy analysts normally
    refer to source pages.
    """

    if importlib.util.find_spec("fitz") is None:
        msg = "PDF loading requires PyMuPDF. Install it with: python -m pip install pymupdf"
        raise RuntimeError(msg)

    import fitz

    source_path = Path(path)
    try:
        pdf = fitz.open(source_path)
    except Exception as exc:  # noqa: BLE001 - normalize parser-specific exceptions.
        msg = f"Unable to open PDF document: {source_path}"
        raise ValueError(msg) from exc

    with pdf:
        return tuple(
            DocumentRecord(
                document_name=source_path.name,
                source_type="pdf",
                source_path=source_path,
                page_number=page_index + 1,
                text=page.get_text("text"),
            )
            for page_index, page in enumerate(pdf)
        )


def load_synthetic_policy_packet_records(
    packet_dir: str | Path | None = None,
) -> tuple[DocumentRecord, ...]:
    """Load the Issue #3 synthetic packet as normalized document records."""

    documents = (
        load_synthetic_policy_packet()
        if packet_dir is None
        else load_synthetic_policy_packet(packet_dir)
    )
    return tuple(
        DocumentRecord(
            document_name=document.path.name,
            source_type="synthetic",
            source_path=document.path,
            page_number=None,
            text=document.text,
        )
        for document in documents
    )


def _iter_document_paths(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    candidates: list[Path] = []
    for path in paths:
        candidate = Path(path)
        if candidate.is_dir():
            candidates.extend(child for child in sorted(candidate.iterdir()) if child.is_file())
        else:
            candidates.append(candidate)
    return tuple(candidates)


def _loader_error_from_exception(path: Path, exc: Exception) -> LoaderError:
    suffix = path.suffix.lower().lstrip(".") or "unknown"
    return LoaderError(
        document_name=path.name or str(path),
        source_type=suffix,
        source_path=path,
        message=str(exc),
    )
