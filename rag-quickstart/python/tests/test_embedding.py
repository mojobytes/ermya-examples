"""Tests for embedding providers: openai, azure-openai, ollama + factory.

HTTP is mocked with requests-mock; no real network calls.
"""

import pytest

from config_loader import EmbeddingConfig
from embedding import (
    AzureOpenAIProvider,
    OllamaProvider,
    OpenAIProvider,
    create_provider,
)


def _cfg(**overrides):
    base = dict(
        provider="openai",
        endpoint="",
        api_key="",
        model="",
        deployment_name="",
        dimension=3,
    )
    base.update(overrides)
    return EmbeddingConfig(**base)


def test_openai_provider_builds_correct_request(requests_mock):
    requests_mock.post(
        "https://api.openai.com/v1/embeddings",
        json={"data": [{"embedding": [0.1, 0.2, 0.3]}]},
    )
    provider = OpenAIProvider(
        _cfg(provider="openai", api_key="sk-test", model="text-embedding-3-small")
    )
    vec = provider.embed("hello world")
    req = requests_mock.last_request
    assert req.headers["Authorization"] == "Bearer sk-test"
    body = req.json()
    assert body["model"] == "text-embedding-3-small"
    assert body["input"] == "hello world"
    assert vec == [0.1, 0.2, 0.3]


def test_azure_openai_provider_builds_correct_request(requests_mock):
    endpoint = "https://myaccount.openai.azure.com"
    deployment = "my-deployment"
    requests_mock.post(
        f"{endpoint}/openai/deployments/{deployment}/embeddings",
        json={"data": [{"embedding": [0.5, 0.6]}]},
    )
    provider = AzureOpenAIProvider(
        _cfg(
            provider="azure-openai",
            endpoint=endpoint,
            api_key="az-key",
            deployment_name=deployment,
            dimension=2,
        )
    )
    vec = provider.embed("test text")
    req = requests_mock.last_request
    assert req.headers["api-key"] == "az-key"
    assert "api-version" in req.qs
    assert req.json()["input"] == "test text"
    assert vec == [0.5, 0.6]


def test_ollama_provider_builds_correct_request_no_auth(requests_mock):
    requests_mock.post(
        "http://localhost:11434/api/embeddings",
        json={"embedding": [0.9, 0.8, 0.7]},
    )
    provider = OllamaProvider(
        _cfg(
            provider="ollama",
            endpoint="http://localhost:11434",
            model="nomic-embed-text",
            api_key="",
        )
    )
    vec = provider.embed("my text")
    req = requests_mock.last_request
    assert "Authorization" not in req.headers
    body = req.json()
    assert body["model"] == "nomic-embed-text"
    assert body["prompt"] == "my text"
    assert vec == [0.9, 0.8, 0.7]


@pytest.mark.parametrize(
    "provider_name,expected_class",
    [
        ("openai", OpenAIProvider),
        ("azure-openai", AzureOpenAIProvider),
        ("ollama", OllamaProvider),
    ],
)
def test_create_provider_returns_correct_class(provider_name, expected_class):
    provider = create_provider(_cfg(provider=provider_name))
    assert isinstance(provider, expected_class)


def test_create_provider_raises_on_unknown():
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        create_provider(_cfg(provider="not-a-provider"))
