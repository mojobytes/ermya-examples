"""RAG quickstart orchestration: parse -> chunk -> embed -> insert -> search.

The Tessera client and embedding provider are injected so the whole flow is
unit-testable without a live Tessera or real HTTP. When ``config.vls`` is set,
the pipeline demonstrates Vector-Level Security: it ingests the fixed PDF
catalog (``documents.DOCUMENTS``) with a per-document owner ACL, then runs the
same query as Alice and as Bob using their real tokens, printing disjoint
result sets. When ``config.vls`` is None, it falls back to the original
vector-only ingest+search over the markdown files in ``data_dir`` so the
example still runs standalone.

Alice/Bob tokens are used only to call ``client.search``; they are never
printed or logged anywhere in this module.
"""

from __future__ import annotations

from pathlib import Path

from chunker import chunk_text, parse_markdown_files
from config_loader import Config
from dimension_check import verify_dimension
from documents import DOCUMENTS
from embedding import EmbeddingProvider
from pdf_extractor import extract_text
from tessera import Permission
from vls import fetch_user_token, register_demo_principals

BANNER = (
    "=" * 64
    + "\n  EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.\n"
    + "=" * 64
)

DEMO_QUERY = "transparency obligations for high-risk AI systems"


def _ingest_documents(client, provider: EmbeddingProvider, config: Config, data_dir: Path) -> list[float] | None:
    """Embed and insert every chunk from the markdown files in ``data_dir``.

    Returns the first vector (for the demo search), or None if there were no
    documents. Used by the standalone (no-VLS) fallback path.
    """
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
    _print_results("(no VLS)", results)


def _print_results(label: str, results) -> None:
    """Print id/distance/jurisdiction for each result. NEVER print a token."""
    print(f"\n[{label}] search returned {len(results)} result(s):")
    for result in results:
        metadata = result.metadata or {} if hasattr(result, "metadata") else {}
        jurisdiction = metadata.get("jurisdiction", "?")
        text = metadata.get("text", "")
        print(
            f"  - id={getattr(result, 'id', '?')} "
            f"distance={getattr(result, 'distance', '?')} "
            f"jurisdiction={jurisdiction}: {text[:60]}"
        )


def _ingest_pdf(client, provider, config: Config, data_dir: Path, doc, extract, permissions):
    """Extract, chunk, embed and insert one PDF document. Returns its first
    vector (or None if it produced no chunks)."""
    text = extract(str(Path(data_dir) / doc.filename))
    chunks = chunk_text(text, config.ingestion.chunk_size, config.ingestion.chunk_overlap)
    first: list[float] | None = None
    for i, chunk in enumerate(chunks):
        vector = provider.embed(chunk)
        if first is None:
            verify_dimension(vector, config.embedding.dimension)
            first = vector
        client.insert(
            tenant_id=config.ingestion.tenant_id,
            vector=vector,
            metadata={
                "text": chunk,
                "source": doc.filename,
                "chunk": i,
                "jurisdiction": doc.jurisdiction,
            },
            permissions=permissions,
        )
    return first


def _run_vls_demo(config: Config, client, provider, data_dir: Path, extract, fetch_token) -> None:
    """Ingest the PDF catalog with a per-document owner ACL, then run the same
    query as each demo user via their own token, printing disjoint results."""
    register_demo_principals(client, config.ingestion.tenant_id)
    for doc in DOCUMENTS:
        perms = [Permission(principal=doc.owner, action="read")]
        _ingest_pdf(client, provider, config, data_dir, doc, extract, perms)

    query_vector = provider.embed(DEMO_QUERY)
    for owner in sorted(config.vls.users):
        token = fetch_token(config.vls, owner)  # never printed/logged
        results = client.search(
            tenant_id=config.ingestion.tenant_id,
            vector=query_vector,
            k=5,
            user_token=token,
        )
        _print_results(owner, results)  # NEVER print the token


def _run_standalone(config: Config, client, provider, data_dir: Path) -> None:
    """Vector-only ingest+search over the markdown files in data_dir, with no
    ACLs. Runs when config.vls is None so the example works standalone."""
    first_vector = _ingest_documents(client, provider, config, data_dir)
    if first_vector is None:
        print(f"No documents found in {data_dir}; nothing ingested.")
        return
    _demo_search(client, config, first_vector)


def run_pipeline(
    config: Config,
    client,
    provider: EmbeddingProvider,
    data_dir: Path,
    *,
    extract=extract_text,
    fetch_token=fetch_user_token,
) -> None:
    """Run the full RAG quickstart with injected client + provider.

    When ``config.vls`` is set, runs the VLS demo (per-doc owner ACL ingest +
    one search per user token). Otherwise falls back to the vector-only
    ingest+search over markdown files in ``data_dir``.
    """
    print(BANNER)
    print(
        f"\nTarget Tessera: {config.tessera.host}:{config.tessera.port} "
        f"(tenant '{config.ingestion.tenant_id}', dimension "
        f"{config.embedding.dimension})"
    )
    print(f"Embedding provider: {config.embedding.provider}\n")

    client.create_tenant(config.ingestion.tenant_id, config.embedding.dimension)

    if config.vls is not None:
        _run_vls_demo(config, client, provider, data_dir, extract, fetch_token)
    else:
        _run_standalone(config, client, provider, data_dir)
