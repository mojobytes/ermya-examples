# Tessera Examples

Runnable example projects for [Tessera](https://github.com/mojobytes), the
vector database. Each example is self-contained: open it, run it, modify it.

> ⚠️ **EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.**
> These examples read API keys from a `tessera_config.json` file in **plaintext**
> by design, so you can run them as-is. **Do not** use this approach in
> production, and **do not** commit `tessera_config.json` (it is git-ignored).

## `rag-quickstart`

A minimal RAG (Retrieval-Augmented Generation) ingestion + search pipeline,
implemented identically in three languages:

| Language   | Folder                       | SDK                    |
|------------|------------------------------|------------------------|
| Python     | `rag-quickstart/python`      | `tessera`              |
| TypeScript | `rag-quickstart/typescript`  | `@tesseradb/client`    |
| C#         | `rag-quickstart/csharp`      | `Tessera.Client`       |

Each one performs the same four stages:

1. **Parse** sample documents from `data/` (Markdown).
2. **Chunk** them deterministically (`chunk_size` / `chunk_overlap`).
3. **Embed** each chunk with a real embedding provider
   (`openai`, `azure-openai`, or `ollama`).
4. **Insert** the vectors into Tessera, then run a **demo search**.

## Configuration

Each example reads its connection and embedding settings from a
`tessera_config.json` file. The [Tessera Launchpad](https://github.com/mojobytes)
writes this file into the repository root when it generates a project for you.

**If `tessera_config.json` is absent, each example falls back to documented
defaults** (local Tessera on `localhost:50051`, Ollama embeddings via
`nomic-embed-text`) so the repo is runnable on its own.

The config file is searched by walking **up** the directory tree from the
example folder to the repository root, so the single file written at the root
serves whichever language you run.

### `tessera_config.json` shape

```json
{
  "_warning": "EXAMPLE PROJECT — API keys are stored in plaintext. NOT production-ready. Do not commit this file.",
  "schema_version": 1,
  "tessera":   { "host": "localhost", "port": 50051, "api_key": "...", "secure": false },
  "embedding": { "provider": "ollama", "endpoint": "http://localhost:11434", "api_key": "", "model": "nomic-embed-text", "deployment_name": "", "dimension": 768 },
  "ingestion": { "tenant_id": "rag-quickstart", "chunk_size": 800, "chunk_overlap": 100, "data_dir": "./data" }
}
```

### Embedding providers

| `provider`     | Auth        | Endpoint                              | Selector field    |
|----------------|-------------|---------------------------------------|-------------------|
| `openai`       | API key     | `https://api.openai.com/v1/embeddings`| `model`           |
| `azure-openai` | API key     | `{endpoint}/openai/deployments/...`   | `deployment_name` |
| `ollama`       | none        | `{endpoint}/api/embeddings` (local)   | `model`           |

`embedding.dimension` is the contract for the vector size. The example uses it
to create the Tessera tenant and **verifies** that the provider actually returns
vectors of that dimension, failing fast with a clear message if they disagree.

## Per-language instructions

See the `README.md` inside each language folder for setup and run commands.
