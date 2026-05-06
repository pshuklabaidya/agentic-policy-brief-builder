from agentic_policy_brief_builder.ingestion.synthetic_packet import load_synthetic_policy_packet


def test_synthetic_policy_packet_loads_demo_documents() -> None:
    documents = load_synthetic_policy_packet()

    assert len(documents) >= 3
    assert [document.path.name for document in documents] == sorted(
        document.path.name for document in documents
    )
    assert all(document.title.startswith("SYNTHETIC DOCUMENT:") for document in documents)
    assert all("Synthetic data notice:" in document.text for document in documents)


def test_synthetic_policy_packet_uses_one_coherent_topic() -> None:
    documents = load_synthetic_policy_packet()

    for document in documents:
        normalized_text = document.text.lower()
        assert "local housing affordability and zoning reform" in normalized_text
        assert "riverton" in normalized_text
