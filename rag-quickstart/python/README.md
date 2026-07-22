# Tessera RAG Quickstart — Python

> ⚠️ **EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.**
> This example reads API keys from `tessera_config.json` in plaintext. Do not
> use this approach in production, and do not commit that file (it is ignored).

A minimal RAG pipeline: parse Markdown from `data/` → chunk → embed → insert
into Tessera → demo search. When a `vls` config block is present, the same
pipeline instead runs a **Vector-Level Security (VLS) demo**: it ingests 11
official AI-governance PDFs with per-document owner ACLs and shows that the
same query returns disjoint result sets for two different users.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PDF extraction uses [`oxidize-pdf`](https://pypi.org/project/oxidize-pdf/)
(pinned in `requirements.txt` / `pyproject.toml`), pulled in automatically by
the commands above. The VLS demo path uses its RAG-oriented semantic chunking
(`rag_chunks()`): chunks respect headings and sections, and each vector's
metadata carries the chunk's heading and page number, so search results cite
where in the document they come from. `chunk_size`/`chunk_overlap` from the
config only apply to the standalone Markdown fallback.

## Configuration

The example reads `tessera_config.json` by walking **up** from this folder to the
repository root (where the Tessera Launchpad writes it). **If the file is
absent, documented defaults are used** — a local Tessera on `localhost:50051`
and local Ollama embeddings (`nomic-embed-text`, dimension 768) — so the example
runs standalone.

To run against Ollama locally with no API keys:

```bash
ollama pull nomic-embed-text
ollama serve   # serves http://localhost:11434
```

To use OpenAI or Azure OpenAI instead, provide a `tessera_config.json` with the
matching `embedding.provider`, `model`/`deployment_name`, `api_key`, and
`dimension`.

## VLS demo (Alice vs. Bob)

`tessera_config.json` accepts an optional `vls` block:

```json
{
  "schema_version": 1,
  "tessera": { "host": "localhost", "port": 50051, "api_key": "", "secure": false },
  "embedding": { "provider": "ollama", "endpoint": "http://localhost:11434", "api_key": "", "model": "nomic-embed-text", "deployment_name": "", "dimension": 768 },
  "ingestion": { "tenant_id": "rag-quickstart", "chunk_size": 800, "chunk_overlap": 100, "data_dir": "./data" },
  "vls": {
    "issuer": "https://keycloak.example.com/realms/demo",
    "token_endpoint": "https://keycloak.example.com/realms/demo/protocol/openid-connect/token",
    "client_id": "rag-quickstart",
    "users": {
      "alice": { "username": "alice", "password": "..." },
      "bob": { "username": "bob", "password": "..." }
    }
  }
}
```

When this block is present, `main()` ingests the fixed 11-document PDF
catalog defined in `documents.py` instead of the Markdown files in `data/`.
Each PDF is owned by exactly one of two demo users:

- **Alice** — Europe + international bodies (EU, UK, UNESCO, OECD, Council of
  Europe)
- **Bob** — Americas + Asia-Pacific (US, Australia, Canada, Singapore, Japan,
  South Korea)

Every document is inserted with a per-document ACL granting `read` only to
its owner. The demo then runs the **same search query** once with Alice's
token and once with Bob's token and prints both result sets — they never
overlap, because Vector-Level Security filters results by the caller's
granted permissions, not just by vector similarity.

User tokens (Alice's/Bob's JWTs) are fetched via an OAuth2 password grant and
are used only to call `client.search`; they are never printed or logged.

**Without a `vls` block**, the example runs standalone exactly as described
above: vector-only ingest + search over the Markdown files in `data/`, no
ACLs, no Keycloak dependency. The `data/*.pdf` corpus and its `SOURCES.md`
provenance table exist specifically to support the VLS demo path; see
[`data/SOURCES.md`](data/SOURCES.md) for where each document came from.

## Run

```bash
python main.py
```

## Test

```bash
pip install -e ".[dev]"
pytest
```

The tests mock the Tessera SDK and the embedding HTTP calls, so they run without
a live Tessera server or network access.

## Layout

| File                        | Responsibility                                  |
|-----------------------------|-------------------------------------------------|
| `config_loader.py`          | Locate + parse `tessera_config.json` or defaults |
| `chunker.py`                | Parse Markdown, deterministic chunking          |
| `embedding.py`              | Provider interface + openai / azure / ollama    |
| `dimension_check.py`        | Verify vector length matches config dimension   |
| `tessera_client_factory.py` | Build the Tessera SDK client from config        |
| `documents.py`              | VLS demo PDF catalog + per-document owner ACL   |
| `pdf_extractor.py`          | PDF extraction via `oxidize-pdf`: plain text + RAG semantic chunks (heading + page provenance) |
| `vls.py`                    | VLS demo helpers: register principals, fetch tokens |
| `pipeline.py`               | Orchestration (injected client + provider); standalone or VLS demo |
| `main.py`                   | Entry point wiring the real implementations     |
| `data/SOURCES.md`           | Provenance for the 11 committed PDF documents   |
