"""Embedding clients for retrieval workflows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from agentic_policy_brief_builder.config import AppConfig

__all__ = [
    "EmbeddingClient",
    "OpenAIEmbeddingClient",
    "validate_embedding_texts",
]


class EmbeddingClient(Protocol):
    """Interface for clients that embed batches of text strings."""

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Return one embedding vector per input text."""


class OpenAIEmbeddingClient:
    """OpenAI-backed embedding client using the configured embedding model."""

    def __init__(
        self,
        config: AppConfig,
        *,
        openai_client: Any | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or config.openai_embedding_model
        if openai_client is None:
            if not config.has_openai_api_key:
                msg = "OPENAI_API_KEY is required to create an OpenAI embedding client"
                raise ValueError(msg)
            from openai import OpenAI

            openai_client = OpenAI(api_key=config.openai_api_key)
        self._client = openai_client

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Embed a non-empty batch of nonblank strings with OpenAI."""

        validated_texts = validate_embedding_texts(texts)
        response = self._client.embeddings.create(
            model=self.model,
            input=list(validated_texts),
        )
        response_data = sorted(response.data, key=lambda item: item.index)
        return tuple(tuple(float(value) for value in item.embedding) for item in response_data)


def validate_embedding_texts(texts: Sequence[str]) -> tuple[str, ...]:
    """Validate text inputs before an embedding request is made."""

    if isinstance(texts, str):
        msg = "texts must be a sequence of strings, not a single string"
        raise TypeError(msg)
    if not texts:
        msg = "texts must contain at least one string"
        raise ValueError(msg)

    validated: list[str] = []
    for index, text in enumerate(texts):
        if not isinstance(text, str):
            msg = f"texts[{index}] must be a string"
            raise TypeError(msg)
        if not text.strip():
            msg = f"texts[{index}] must not be blank"
            raise ValueError(msg)
        validated.append(text)

    return tuple(validated)
