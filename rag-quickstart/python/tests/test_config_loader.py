"""Tests for config_loader: reads tessera_config.json (walk-up) or defaults."""

import json

import pytest

from config_loader import load_config

MINIMAL_CONFIG = {
    "_warning": "w",
    "schema_version": 1,
    "tessera": {"host": "myhost", "port": 9999, "api_key": "k", "secure": False},
    "embedding": {
        "provider": "openai",
        "endpoint": "",
        "api_key": "ek",
        "model": "text-embedding-3-small",
        "deployment_name": "",
        "dimension": 1536,
    },
    "ingestion": {
        "tenant_id": "t1",
        "chunk_size": 800,
        "chunk_overlap": 100,
        "data_dir": "./data",
    },
}


def _write_config(directory, data=MINIMAL_CONFIG):
    (directory / "tessera_config.json").write_text(json.dumps(data))


def test_load_config_reads_tessera_block(tmp_path):
    _write_config(tmp_path)
    config = load_config(start_dir=tmp_path)
    assert config.tessera.host == "myhost"
    assert config.tessera.port == 9999
    assert config.tessera.api_key == "k"
    assert config.tessera.secure is False


def test_load_config_reads_embedding_and_ingestion(tmp_path):
    _write_config(tmp_path)
    config = load_config(start_dir=tmp_path)
    assert config.embedding.provider == "openai"
    assert config.embedding.model == "text-embedding-3-small"
    assert config.embedding.dimension == 1536
    assert config.ingestion.tenant_id == "t1"
    assert config.ingestion.chunk_size == 800
    assert config.ingestion.chunk_overlap == 100


def test_load_config_returns_defaults_when_absent(tmp_path):
    config = load_config(start_dir=tmp_path)
    assert config.tessera.host == "localhost"
    assert config.tessera.port == 50051
    assert config.tessera.secure is False
    assert config.embedding.provider == "ollama"
    assert config.embedding.endpoint == "http://localhost:11434"
    assert config.embedding.model == "nomic-embed-text"
    assert config.embedding.dimension == 768
    assert config.ingestion.tenant_id == "rag-quickstart"
    assert config.ingestion.chunk_size == 800
    assert config.ingestion.chunk_overlap == 100
    assert config.ingestion.data_dir == "./data"


def test_load_config_walks_up_to_find_file(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    _write_config(tmp_path)
    config = load_config(start_dir=nested)
    assert config.tessera.host == "myhost"


def test_load_config_raises_on_unknown_schema_version(tmp_path):
    bad = dict(MINIMAL_CONFIG, schema_version=99)
    _write_config(tmp_path, bad)
    with pytest.raises(ValueError, match="schema_version"):
        load_config(start_dir=tmp_path)
