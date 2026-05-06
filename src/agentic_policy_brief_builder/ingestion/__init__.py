"""Document ingestion helpers for policy brief generation."""

from agentic_policy_brief_builder.ingestion.loaders import (
    DocumentLoadResult,
    DocumentRecord,
    LoaderError,
    load_document,
    load_documents,
    load_pdf_document,
    load_synthetic_policy_packet_records,
    load_txt_document,
)
from agentic_policy_brief_builder.ingestion.synthetic_packet import (
    SyntheticPolicyDocument,
    load_synthetic_policy_packet,
)

__all__ = [
    "DocumentLoadResult",
    "DocumentRecord",
    "LoaderError",
    "SyntheticPolicyDocument",
    "load_document",
    "load_documents",
    "load_pdf_document",
    "load_synthetic_policy_packet",
    "load_synthetic_policy_packet_records",
    "load_txt_document",
]
