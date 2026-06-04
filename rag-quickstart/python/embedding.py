"""Real embedding providers selectable by config: openai, azure-openai, ollama.

Each provider implements EmbeddingProvider.embed(text) -> list[float] by calling
the provider's real HTTP embeddings API. The provider is chosen from
embedding.provider via create_provider().
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import requests

from config_loader import EmbeddingConfig

AZURE_API_VERSION = "2024-02-01"
HTTP_TIMEOUT_SECONDS = 60


@runtime_checkable
class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        """Return the embedding vector for ``text``."""
        ...


class OpenAIProvider:
    """OpenAI embeddings API (https://api.openai.com/v1/embeddings)."""

    def __init__(self, config: EmbeddingConfig):
        self._config = config

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self._config.api_key}"},
            json={"model": self._config.model, "input": text},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


class AzureOpenAIProvider:
    """Azure OpenAI embeddings (deployment-scoped URL, ``api-key`` header)."""

    def __init__(self, config: EmbeddingConfig):
        self._config = config

    def embed(self, text: str) -> list[float]:
        endpoint = self._config.endpoint.rstrip("/")
        url = (
            f"{endpoint}/openai/deployments/"
            f"{self._config.deployment_name}/embeddings"
        )
        response = requests.post(
            url,
            params={"api-version": AZURE_API_VERSION},
            headers={"api-key": self._config.api_key},
            json={"input": text},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


class OllamaProvider:
    """Local Ollama embeddings (no API key, POST /api/embeddings)."""

    def __init__(self, config: EmbeddingConfig):
        self._config = config

    def embed(self, text: str) -> list[float]:
        endpoint = self._config.endpoint.rstrip("/")
        response = requests.post(
            f"{endpoint}/api/embeddings",
            json={"model": self._config.model, "prompt": text},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["embedding"]


PROVIDER_REGISTRY: dict[str, type] = {
    "openai": OpenAIProvider,
    "azure-openai": AzureOpenAIProvider,
    "ollama": OllamaProvider,
}


def create_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    """Return the provider implementation selected by ``config.provider``."""
    provider_class = PROVIDER_REGISTRY.get(config.provider)
    if provider_class is None:
        raise ValueError(
            f"Unknown embedding provider: {config.provider!r}. "
            f"Supported: {', '.join(sorted(PROVIDER_REGISTRY))}."
        )
    return provider_class(config)
