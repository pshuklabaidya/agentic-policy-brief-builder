"""Streamlit entry point for Agentic Policy Brief Builder."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal, Protocol
from uuid import uuid4

import streamlit as st

from agentic_policy_brief_builder.audit import CitationAuditResult, audit_policy_brief_citations
from agentic_policy_brief_builder.config import (
    AppConfig,
    format_missing_config_message,
    load_config,
)
from agentic_policy_brief_builder.drafting import (
    BriefSection,
    PolicyBriefDraft,
    draft_policy_brief,
)
from agentic_policy_brief_builder.ingestion import (
    DocumentRecord,
    LoaderError,
    chunk_document_records,
    load_documents,
    load_synthetic_policy_packet_records,
)
from agentic_policy_brief_builder.retrieval import (
    LocalChromaVectorStore,
    OpenAIEmbeddingClient,
    RetrievalResult,
)
from agentic_policy_brief_builder.ui import (
    citation_audit_to_markdown,
    policy_brief_to_markdown,
    policy_brief_to_pdf_bytes,
    policy_brief_to_text,
    retrieved_evidence_to_markdown,
)

DocumentSource = Literal["synthetic", "upload"]


class UploadedPolicyFile(Protocol):
    """Streamlit uploaded-file fields used by the app."""

    name: str

    def getbuffer(self) -> memoryview: ...



def main() -> None:
    st.set_page_config(
        page_title="Agentic Policy Brief Builder",
        page_icon="📄",
        layout="wide",
    )

    st.title("Agentic Policy Brief Builder")
    st.caption(
        "Agentic RAG app for cited policy briefs with risk review and citation auditing."
    )

    config = load_config(streamlit_secrets=st.secrets)
    missing_config_message = format_missing_config_message(config)
    if missing_config_message:
        st.error(missing_config_message)
    else:
        st.success(
            "Configuration loaded. OpenAI and vector-store settings are ready for the "
            f"{config.app_env} environment."
        )

    document_source = st.radio(
        "Document source",
        options=("synthetic", "upload"),
        format_func=lambda value: "Use synthetic policy packet"
        if value == "synthetic"
        else "Upload TXT/PDF policy documents",
        horizontal=True,
    )

    uploaded_files = st.file_uploader(
        "Upload TXT/PDF policy documents",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        disabled=document_source != "upload",
    )

    policy_question = st.text_area(
        "Policy question",
        placeholder="What are the main tradeoffs in the proposed policy?",
    )

    top_k = st.slider(
        "Top-k evidence results",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        help="Number of retrieved evidence chunks to pass into drafting and citation audit.",
    )

    if st.button("Generate cited policy brief", type="primary"):
        _run_policy_brief_workflow(
            config=config,
            missing_config_message=missing_config_message,
            document_source=document_source,
            uploaded_files=uploaded_files,
            policy_question=policy_question,
            top_k=top_k,
        )

    st.divider()
    st.caption(
        "This tool is a document-grounded research aid. It does not provide legal, "
        "regulatory, lobbying, or financial advice."
    )


def _run_policy_brief_workflow(
    *,
    config: AppConfig,
    missing_config_message: str | None,
    document_source: DocumentSource,
    uploaded_files: list[UploadedPolicyFile] | None,
    policy_question: str,
    top_k: int,
) -> None:
    if missing_config_message:
        st.error(missing_config_message)
        return
    if not policy_question.strip():
        st.warning("Enter a policy question before generating a policy brief.")
        return

    with st.status("Generating cited policy brief...", expanded=True) as status:
        records, loader_errors = _load_selected_documents(document_source, uploaded_files)
        _display_loader_errors(loader_errors)
        if not records:
            status.update(label="No documents available", state="error")
            st.warning("No policy documents are available for the selected source.")
            return
        st.write(f"Loaded {len(records)} document record(s).")

        chunks = chunk_document_records(records)
        if not chunks:
            status.update(label="No document text available", state="error")
            st.warning("No non-empty document text was available to chunk and retrieve.")
            return
        st.write(f"Created {len(chunks)} retrieval chunk(s).")

        try:
            embedding_client = OpenAIEmbeddingClient(config)
            vector_store = LocalChromaVectorStore(
                config,
                embedding_client,
                collection_name=f"policy-evidence-{uuid4().hex[:12]}",
            )
            indexed_count = vector_store.index_chunks(chunks)
            retrieved_results = vector_store.retrieve_relevant_chunks(
                policy_question,
                top_k=top_k,
            )
        except Exception as exc:  # noqa: BLE001 - surface pipeline errors in the UI.
            status.update(label="Retrieval failed", state="error")
            st.error(f"Retrieval failed: {exc}")
            return

        st.write(f"Indexed {indexed_count} chunk(s).")
        if not retrieved_results:
            status.update(label="No evidence retrieved", state="error")
            st.warning("Retrieval returned no relevant evidence, so no brief was generated.")
            return
        st.write(f"Retrieved {len(retrieved_results)} evidence result(s).")

        try:
            draft = draft_policy_brief(
                policy_question,
                retrieved_results,
                config=config,
            )
            audit = audit_policy_brief_citations(draft, retrieved_results)
        except Exception as exc:  # noqa: BLE001 - keep Streamlit guardrails user-facing.
            status.update(label="Drafting or citation audit failed", state="error")
            st.error(f"Drafting or citation audit failed: {exc}")
            return

        status.update(label="Policy brief generated", state="complete")

    _display_retrieved_evidence(retrieved_results)
    _display_policy_brief(draft)
    _display_citation_audit(audit)
    _display_export_downloads(draft, retrieved_results, audit)


def _load_selected_documents(
    document_source: DocumentSource,
    uploaded_files: list[UploadedPolicyFile] | None,
) -> tuple[tuple[DocumentRecord, ...], tuple[LoaderError, ...]]:
    if document_source == "synthetic":
        try:
            return load_synthetic_policy_packet_records(), ()
        except Exception as exc:  # noqa: BLE001 - loader failures are shown, not raised.
            return (), (
                LoaderError(
                    document_name="synthetic policy packet",
                    source_type="synthetic",
                    message=str(exc),
                ),
            )

    if not uploaded_files:
        return (), ()

    with tempfile.TemporaryDirectory(prefix="policy-brief-upload-") as temp_dir:
        upload_paths = tuple(
            _save_uploaded_file(uploaded_file, Path(temp_dir))
            for uploaded_file in uploaded_files
        )
        load_result = load_documents(upload_paths)
        return load_result.records, load_result.errors


def _save_uploaded_file(uploaded_file: UploadedPolicyFile, temp_dir: Path) -> Path:
    filename = Path(uploaded_file.name).name
    upload_path = temp_dir / filename
    data = uploaded_file.getbuffer()
    upload_path.write_bytes(bytes(data))
    return upload_path


def _display_loader_errors(loader_errors: tuple[LoaderError, ...]) -> None:
    if not loader_errors:
        return
    st.warning("Some documents could not be loaded.")
    for error in loader_errors:
        st.error(f"{error.document_name} ({error.source_type}): {error.message}")


def _display_retrieved_evidence(retrieved_results: tuple[RetrievalResult, ...]) -> None:
    st.header("Retrieved Evidence")
    if not retrieved_results:
        st.warning("No evidence was retrieved.")
        return

    for result in retrieved_results:
        page_label = f", page {result.page_number}" if result.page_number is not None else ""
        with st.expander(f"{result.rank}. {result.evidence_id}"):
            st.caption(
                f"{result.document_name} ({result.source_type}{page_label}, "
                f"chunk {result.chunk_index})"
            )
            st.write(result.text)


def _display_policy_brief(draft: PolicyBriefDraft) -> None:
    st.header(draft.title)
    st.subheader("Executive Summary")
    st.write(draft.executive_summary)

    _display_sections("Key Findings", draft.key_findings)
    _display_sections("Policy Options", draft.policy_options)
    _display_sections("Risks and Tradeoffs", draft.risks_and_tradeoffs)

    st.subheader("Recommendation")
    _display_section(draft.recommendation)

    st.subheader("Evidence Used")
    if not draft.evidence_used:
        st.error("No cited evidence was recorded for this draft.")
        return
    for citation in draft.evidence_used:
        page_label = f", page {citation.page_number}" if citation.page_number is not None else ""
        st.markdown(
            f"- `{citation.evidence_id}` — {citation.document_name} "
            f"({citation.source_type}{page_label}, chunk {citation.chunk_index})"
        )


def _display_sections(title: str, sections: tuple[BriefSection, ...]) -> None:
    st.subheader(title)
    for section in sections:
        _display_section(section)


def _display_section(section: BriefSection) -> None:
    st.markdown(f"**{section.heading}**")
    st.write(section.content)
    if section.evidence_ids:
        evidence_ids = ", ".join(f"`{evidence_id}`" for evidence_id in section.evidence_ids)
        st.caption("Evidence IDs: " + evidence_ids)
    else:
        st.error("This section has no cited evidence IDs.")


def _display_citation_audit(audit: CitationAuditResult) -> None:
    st.header("Citation Audit")
    if audit.passed:
        st.success("Citation audit passed.")
    else:
        st.error("Citation audit failed.")

    st.subheader("Citation Audit Findings")
    if audit.findings:
        for finding in audit.findings:
            st.markdown(
                f"- **{finding.severity.value.upper()}** `{finding.code}`: "
                f"{finding.message}"
            )
    else:
        st.write("No citation audit findings.")

    st.subheader("Unused Evidence IDs")
    if audit.unused_evidence_ids:
        st.write(", ".join(f"`{evidence_id}`" for evidence_id in audit.unused_evidence_ids))
    else:
        st.write("None")


def _display_export_downloads(
    draft: PolicyBriefDraft,
    retrieved_results: tuple[RetrievalResult, ...],
    audit: CitationAuditResult,
) -> None:
    markdown_export = "\n\n".join(
        (
            policy_brief_to_markdown(draft).strip(),
            retrieved_evidence_to_markdown(retrieved_results).strip(),
            citation_audit_to_markdown(audit).strip(),
        )
    )
    text_export = policy_brief_to_text(draft, retrieved_results, audit)
    pdf_export = policy_brief_to_pdf_bytes(draft, retrieved_results, audit)

    st.download_button(
        "Download Markdown",
        data=markdown_export + "\n",
        file_name="policy_brief.md",
        mime="text/markdown",
        key="download-policy-brief-markdown",
    )
    st.download_button(
        "Download TXT",
        data=text_export,
        file_name="policy_brief.txt",
        mime="text/plain",
        key="download-policy-brief-txt",
    )
    st.download_button(
        "Download PDF",
        data=pdf_export,
        file_name="policy_brief.pdf",
        mime="application/pdf",
        key="download-policy-brief-pdf",
    )


if __name__ == "__main__":
    main()
