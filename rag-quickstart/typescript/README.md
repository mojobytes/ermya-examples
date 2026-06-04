# Tessera RAG Quickstart — TypeScript

> ⚠️ **EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.**
> This example reads API keys from `tessera_config.json` in plaintext. Do not
> use this approach in production, and do not commit that file (it is ignored).

A minimal RAG pipeline: parse Markdown from `data/` → chunk → embed → insert
into Tessera → demo search.

## Setup

```bash
npm install
```

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
matching `embedding.provider`, `model`/`deploymentName`, `apiKey`, and
`dimension`.

## Run

```bash
npm start
```

## Test

```bash
npm test
```

The tests mock the Tessera SDK and the embedding HTTP calls (via `fetch`), so
they run without a live Tessera server or network access.

## Layout

| File                            | Responsibility                                  |
|---------------------------------|-------------------------------------------------|
| `src/config-loader.ts`          | Locate + parse `tessera_config.json` or defaults |
| `src/chunker.ts`                | Parse Markdown, deterministic chunking          |
| `src/embedding.ts`              | Provider interface + openai / azure / ollama    |
| `src/dimension-check.ts`        | Verify vector length matches config dimension   |
| `src/endpoint.ts`               | Compose the scheme-prefixed endpoint URL        |
| `src/tessera-client-factory.ts` | Build the Tessera SDK client from config        |
| `src/pipeline.ts`               | Orchestration (injected client + provider)      |
| `src/main.ts`                   | Entry point wiring the real implementations     |
