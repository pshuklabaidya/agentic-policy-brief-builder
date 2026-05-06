"""Deterministic evidence identifiers for retrieval chunks."""

from __future__ import annotations

import re

_DEFAULT_DOCUMENT_SLUG = "document"
_NON_ALPHANUMERIC_RE = re.compile(r"[^a-z0-9]+")


def document_slug(document_name: str) -> str:
    """Return a deterministic, human-readable slug for a document name.

    File extensions are omitted so evidence IDs stay concise while remaining
    recognizable to analysts reviewing citations.
    """

    normalized_name = document_name.strip().replace("\\", "/")
    basename = normalized_name.rsplit("/", maxsplit=1)[-1]
    slug_source = basename.rsplit(".", maxsplit=1)[0] if "." in basename else basename
    slug = _NON_ALPHANUMERIC_RE.sub("-", slug_source.lower()).strip("-")
    return slug or _DEFAULT_DOCUMENT_SLUG


def evidence_page_or_section(page_number: int | None) -> str:
    """Return the page/section segment used in an evidence ID."""

    if page_number is None:
        return "section"
    return f"page-{page_number}"


def build_evidence_id(document_name: str, page_number: int | None, chunk_index: int) -> str:
    """Build a stable evidence ID for a source document chunk.

    Evidence IDs use the Issue #5 format:
    ``EVID-{document_slug}-{page_or_section}-{chunk_index}``.
    """

    if chunk_index < 0:
        msg = "chunk_index must be greater than or equal to 0"
        raise ValueError(msg)
    if page_number is not None and page_number < 1:
        msg = "page_number must be greater than or equal to 1 when provided"
        raise ValueError(msg)

    return "-".join(
        (
            "EVID",
            document_slug(document_name),
            evidence_page_or_section(page_number),
            str(chunk_index),
        )
    )
