"""Load tessera_config.json by walking up to the repo root, or fall back to
documented defaults so the example runs standalone.

The Tessera Launchpad writes tessera_config.json into the repository root when
it generates this project. Examples live in rag-quickstart/<lang>/, so we search
upward from the start directory to find it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAME = "tessera_config.json"
SUPPORTED_SCHEMA_VERSION = 1


@dataclass
class TesseraConfig:
    host: str
    port: int
    api_key: str
    secure: bool


@dataclass
class EmbeddingConfig:
    provider: str
    endpoint: str
    api_key: str
    model: str
    deployment_name: str
    dimension: int


@dataclass
class IngestionConfig:
    tenant_id: str
    chunk_size: int
    chunk_overlap: int
    data_dir: str


@dataclass
class Config:
    tessera: TesseraConfig
    embedding: EmbeddingConfig
    ingestion: IngestionConfig


def _default_config() -> Config:
    """Documented defaults: local Tessera + local Ollama, no API keys required."""
    return Config(
        tessera=TesseraConfig(
            host="localhost", port=50051, api_key="", secure=False
        ),
        embedding=EmbeddingConfig(
            provider="ollama",
            endpoint="http://localhost:11434",
            api_key="",
            model="nomic-embed-text",
            deployment_name="",
            dimension=768,
        ),
        ingestion=IngestionConfig(
            tenant_id="rag-quickstart",
            chunk_size=800,
            chunk_overlap=100,
            data_dir="./data",
        ),
    )


def _find_config_file(start_dir: Path) -> Path | None:
    current = start_dir.resolve()
    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def _parse_config(data: dict) -> Config:
    version = data.get("schema_version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version {version!r}; "
            f"this example supports schema_version {SUPPORTED_SCHEMA_VERSION}."
        )
    t = data["tessera"]
    e = data["embedding"]
    i = data["ingestion"]
    return Config(
        tessera=TesseraConfig(
            host=t["host"],
            port=int(t["port"]),
            api_key=t.get("api_key", ""),
            secure=bool(t.get("secure", False)),
        ),
        embedding=EmbeddingConfig(
            provider=e["provider"],
            endpoint=e.get("endpoint", ""),
            api_key=e.get("api_key", ""),
            model=e.get("model", ""),
            deployment_name=e.get("deployment_name", ""),
            dimension=int(e["dimension"]),
        ),
        ingestion=IngestionConfig(
            tenant_id=i["tenant_id"],
            chunk_size=int(i["chunk_size"]),
            chunk_overlap=int(i["chunk_overlap"]),
            data_dir=i.get("data_dir", "./data"),
        ),
    )


def load_config(start_dir: Path | None = None) -> Config:
    """Return the parsed config, or documented defaults if no file is found."""
    start = Path(start_dir) if start_dir is not None else Path.cwd()
    config_path = _find_config_file(start)
    if config_path is None:
        return _default_config()
    data = json.loads(config_path.read_text())
    return _parse_config(data)
