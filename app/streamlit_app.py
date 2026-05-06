"""Streamlit entry point for Agentic Policy Brief Builder."""

from __future__ import annotations

import streamlit as st

from agentic_policy_brief_builder.config import format_missing_config_message, load_config


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

    st.info(
        "MVP build baseline: ingestion, retrieval, agents, and citation audit "
        "will be added in upcoming issues."
    )

    uploaded_files = st.file_uploader(
        "Upload policy documents",
        type=["txt", "pdf"],
        accept_multiple_files=True,
    )

    policy_question = st.text_area(
        "Policy question",
        placeholder="What are the main tradeoffs in the proposed policy?",
    )

    if st.button("Generate cited policy brief", type="primary"):
        if missing_config_message:
            st.error(missing_config_message)
            return
        if not uploaded_files:
            st.warning("Upload at least one TXT or PDF policy document.")
            return
        if not policy_question.strip():
            st.warning("Enter a policy question.")
            return

        st.success("Baseline UI is working. Agentic RAG workflow will be added next.")

    st.divider()
    st.caption(
        "This tool is a document-grounded research aid. It does not provide legal, "
        "regulatory, lobbying, or financial advice."
    )


if __name__ == "__main__":
    main()