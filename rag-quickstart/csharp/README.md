# Tessera RAG Quickstart — C#

> ⚠️ **EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.**
> This example reads API keys from `tessera_config.json` in plaintext. Do not
> use this approach in production, and do not commit that file (it is ignored).

A minimal RAG pipeline: parse Markdown from `data/` → chunk → embed → insert
into Tessera → demo search.

## Setup

```bash
dotnet restore
```

## Configuration

The example reads `tessera_config.json` by walking **up** from the run directory
to the repository root (where the Tessera Launchpad writes it). **If the file is
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

## Run

```bash
dotnet run --project src/RagQuickstart
```

## Test

```bash
dotnet test
```

The tests mock the Tessera client (via the `ITesseraClient` interface and Moq)
and the embedding HTTP calls (via a fake `HttpMessageHandler`), so they run
without a live Tessera server or network access.

## Layout

| File                          | Responsibility                                  |
|-------------------------------|-------------------------------------------------|
| `src/RagQuickstart/Config.cs`            | Config records (JSON-mapped)         |
| `src/RagQuickstart/ConfigLoader.cs`      | Locate + parse config or defaults    |
| `src/RagQuickstart/Chunker.cs`           | Parse Markdown, deterministic chunking |
| `src/RagQuickstart/EmbeddingProvider.cs` | Provider interface + openai/azure/ollama |
| `src/RagQuickstart/DimensionCheck.cs`    | Verify vector length vs config dimension |
| `src/RagQuickstart/Endpoint.cs`          | Compose the scheme-prefixed endpoint URL |
| `src/RagQuickstart/ITesseraClient.cs`    | Example-facing client interface + DTOs |
| `src/RagQuickstart/TesseraClientAdapter.cs` | Adapter over the real SDK         |
| `src/RagQuickstart/Pipeline.cs`          | Orchestration (injected client + provider) |
| `src/RagQuickstart/Program.cs`           | Entry point wiring real implementations |
