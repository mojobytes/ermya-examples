"""RAG quickstart orchestration: parse -> chunk -> embed -> insert -> search.

The Tessera client and embedding provider are injected so the whole flow is
unit-testable without a live Tessera or real HTTP. ``main()`` wires the real
implementations from config.
"""

from __future__ import annotations

from pathlib import Path

from chunker import chunk_text, parse_markdown_files
from config_loader import Config
from dimension_check import verify_dimension
from embedding import EmbeddingProvider

BANNER = (
    "=" * 64
    + "\n  EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.\n"
    + "=" * 64
)


def _ingest_documents(client, provider: EmbeddingProvider, config: Config, data_dir: Path) -> list[float] | None:
    """Embed and insert every chunk. Returns the first vector (for the demo
    search), or None if there were no documents."""
    documents = parse_markdown_files(Path(data_dir))
    first_vector: list[float] | None = None
    dimension = config.embedding.dimension
    tenant_id = config.ingestion.tenant_id

    for source_index, document in enumerate(documents):
        chunks = chunk_text(
            document,
            chunk_size=config.ingestion.chunk_size,
            chunk_overlap=config.ingestion.chunk_overlap,
        )
        for chunk_index, chunk in enumerate(chunks):
            vector = provider.embed(chunk)
            if first_vector is None:
                # Fail fast before inserting anything if the model disagrees
                # with the configured dimension.
                verify_dimension(vector, dimension)
                first_vector = vector
            client.insert(
                tenant_id=tenant_id,
                vector=vector,
                metadata={
                    "text": chunk,
                    "source": f"doc:{source_index}",
                    "chunk": chunk_index,
                },
            )
    return first_vector


def _demo_search(client, config: Config, query_vector: list[float]) -> None:
    results = client.search(
        tenant_id=config.ingestion.tenant_id, vector=query_vector, k=5
    )
    print(f"\nDemo search returned {len(results)} result(s):")
    for result in results:
        text = (result.metadata or {}).get("text", "") if hasattr(result, "metadata") else ""
        print(f"  - id={getattr(result, 'id', '?')} distance={getattr(result, 'distance', '?')}: {text[:60]}")


def run_pipeline(config: Config, client, provider: EmbeddingProvider, data_dir: Path) -> None:
    """Run the full RAG quickstart with injected client + provider."""
    print(BANNER)
    print(
        f"\nTarget Tessera: {config.tessera.host}:{config.tessera.port} "
        f"(tenant '{config.ingestion.tenant_id}', dimension "
        f"{config.embedding.dimension})"
    )
    print(f"Embedding provider: {config.embedding.provider}\n")

    client.create_tenant(config.ingestion.tenant_id, config.embedding.dimension)

    first_vector = _ingest_documents(client, provider, config, data_dir)
    if first_vector is None:
        print(f"No documents found in {data_dir}; nothing ingested.")
        return

    _demo_search(client, config, first_vector)
