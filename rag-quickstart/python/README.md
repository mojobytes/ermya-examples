# Tessera RAG Quickstart — Python

> ⚠️ **EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.**
> This example reads API keys from `tessera_config.json` in plaintext. Do not
> use this approach in production, and do not commit that file (it is ignored).

A minimal RAG pipeline: parse Markdown from `data/` → chunk → embed → insert
into Tessera → demo search.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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
matching `embedding.provider`, `model`/`deployment_name`, `api_key`, and
`dimension`.

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
| `pipeline.py`               | Orchestration (injected client + provider)      |
| `main.py`                   | Entry point wiring the real implementations     |
