"""RAG quickstart entry point.

Reads tessera_config.json (or documented defaults), builds the real Tessera
client and embedding provider, and runs the ingest + demo-search pipeline.

Run:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

from config_loader import load_config
from embedding import create_provider
from pipeline import run_pipeline
from tessera_client_factory import create_client


def main() -> None:
    config = load_config()
    client = create_client(config.tessera)
    provider = create_provider(config.embedding)

    data_dir = Path(__file__).parent / config.ingestion.data_dir
    run_pipeline(config, client, provider, data_dir)


if __name__ == "__main__":
    main()
