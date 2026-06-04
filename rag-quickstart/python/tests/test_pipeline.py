"""Tests for the orchestration pipeline.

The Tessera client and embedding provider are injected, so the whole flow is
exercised with mocks — no live Tessera, no real HTTP.
"""

from unittest.mock import MagicMock

import pytest

from config_loader import (
    Config,
    EmbeddingConfig,
    IngestionConfig,
    TesseraConfig,
)
from pipeline import run_pipeline


def make_config(dimension=4, tenant_id="rag-quickstart", chunk_size=10, chunk_overlap=0):
    return Config(
        tessera=TesseraConfig(host="localhost", port=50051, api_key="k", secure=False),
        embedding=EmbeddingConfig(
            provider="ollama",
            endpoint="http://localhost:11434",
            api_key="",
            model="nomic-embed-text",
            deployment_name="",
            dimension=dimension,
        ),
        ingestion=IngestionConfig(
            tenant_id=tenant_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            data_dir="./data",
        ),
    )


@pytest.fixture
def data_dir(tmp_path):
    # 20 chars -> with chunk_size=10, overlap=0 => exactly 2 chunks.
    (tmp_path / "doc.md").write_text("abcdefghijABCDEFGHIJ")
    return tmp_path


@pytest.fixture
def client():
    c = MagicMock()
    c.insert.return_value = 1
    c.search.return_value = []
    return c


@pytest.fixture
def provider():
    p = MagicMock()
    p.embed.return_value = [0.5, 0.5, 0.5, 0.5]  # dimension 4
    return p


def test_pipeline_prints_plaintext_banner(capsys, client, provider, data_dir):
    run_pipeline(make_config(), client, provider, data_dir)
    out = capsys.readouterr().out
    assert "QUICKSTART" in out.upper() or "EXAMPLE" in out.upper()
    assert "plaintext" in out.lower() or "not production" in out.lower()


def test_pipeline_creates_tenant_with_config_dimension(client, provider, data_dir):
    run_pipeline(make_config(dimension=4, tenant_id="my-tenant"), client, provider, data_dir)
    client.create_tenant.assert_called_once_with("my-tenant", 4)


def test_pipeline_embeds_each_chunk(client, provider, data_dir):
    run_pipeline(make_config(chunk_size=10, chunk_overlap=0), client, provider, data_dir)
    assert provider.embed.call_count == 2


def test_pipeline_verifies_dimension_after_first_embed(client, provider, data_dir):
    provider.embed.return_value = [0.1] * 384  # wrong dimension
    with pytest.raises(ValueError, match="Dimension mismatch"):
        run_pipeline(make_config(dimension=1536), client, provider, data_dir)
    # must fail fast, before inserting anything
    client.insert.assert_not_called()


def test_pipeline_inserts_each_chunk_with_metadata(client, provider, data_dir):
    run_pipeline(make_config(dimension=4, tenant_id="t1"), client, provider, data_dir)
    assert client.insert.call_count == 2
    for call in client.insert.call_args_list:
        args, kwargs = call
        tenant = kwargs.get("tenant_id", args[0] if args else None)
        vector = kwargs.get("vector", args[1] if len(args) > 1 else None)
        metadata = kwargs.get("metadata", args[2] if len(args) > 2 else None)
        assert tenant == "t1"
        assert len(vector) == 4
        assert "text" in metadata
        assert "source" in metadata


def test_pipeline_runs_demo_search(client, provider, data_dir):
    run_pipeline(make_config(dimension=4), client, provider, data_dir)
    assert client.search.called


def test_pipeline_no_documents_does_not_insert(client, provider, tmp_path):
    # empty data dir -> no chunks -> no embeds/inserts, but should not crash
    run_pipeline(make_config(), client, provider, tmp_path)
    provider.embed.assert_not_called()
    client.insert.assert_not_called()
