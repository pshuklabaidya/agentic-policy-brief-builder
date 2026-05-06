from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_policy_brief_builder.config import AppConfig
from agentic_policy_brief_builder.retrieval.embeddings import (
    OpenAIEmbeddingClient,
    validate_embedding_texts,
)


@dataclass(frozen=True, slots=True)
class _FakeEmbeddingDatum:
    index: int
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class _FakeEmbeddingResponse:
    data: list[_FakeEmbeddingDatum]


class _FakeEmbeddingsResource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def create(self, *, model: str, input: list[str]) -> _FakeEmbeddingResponse:
        self.calls.append((model, input))
        return _FakeEmbeddingResponse(
            data=[
                _FakeEmbeddingDatum(index=index, embedding=[float(len(text)), float(index)])
                for index, text in enumerate(input)
            ]
        )


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddingsResource()


def test_openai_embedding_client_batches_strings_with_configured_model() -> None:
    fake_openai_client = _FakeOpenAIClient()
    config = AppConfig(openai_api_key="test-key", openai_embedding_model="fake-embedding-model")
    client = OpenAIEmbeddingClient(config, openai_client=fake_openai_client)

    embeddings = client.embed_texts(("housing", "zoning reform"))

    assert embeddings == ((7.0, 0.0), (13.0, 1.0))
    assert fake_openai_client.embeddings.calls == [
        ("fake-embedding-model", ["housing", "zoning reform"])
    ]


@pytest.mark.parametrize("texts", [(), ("",), ("   ",), ("valid", "\n\t")])
def test_embedding_text_validation_rejects_empty_or_blank_input(texts: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        validate_embedding_texts(texts)


def test_embedding_text_validation_rejects_single_string_input() -> None:
    with pytest.raises(TypeError, match="not a single string"):
        validate_embedding_texts("housing")  # type: ignore[arg-type]


def test_openai_embedding_client_rejects_missing_api_key_when_no_client_is_injected() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIEmbeddingClient(AppConfig(openai_api_key=None))
