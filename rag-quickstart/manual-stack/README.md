# Manual stack for the VLS demo (debug / by-hand path)

Runs the same stack Ermya Launchpad deploys (Postgres + Keycloak + Ermya)
without the Launchpad app, so the `rag-quickstart/python` VLS demo can be
launched by hand. The artifacts are **generated with Launchpad's own
generators** — never written by hand — so this path cannot drift from what
Launchpad produces.

The generated files (`docker-compose.yml`, `.env`, `keycloak/ermya-realm.json`,
`ermya_config.json`) carry per-run secrets and are gitignored. Regenerate
them locally:

## 1. Generate the artifacts

Create a scratch Rust binary that depends on the launchpad crate by path and
calls its generators (`generate_compose`, `generate_env`, `generate_realm`,
`build_example_config`). Reference implementation used on 2026-07-22:

```toml
# Cargo.toml
[package]
name = "genstack"
version = "0.1.0"
edition = "2021"

[dependencies]
ermya-launchpad = { path = "<repo-root>/ermya-launchpad/src-tauri" }
serde_json = "1"

[workspace]
```

The `main.rs` builds a `GenerateConfigInput` with services
`["ermya", "postgres"]`, `jwt_enabled: true` and empty `jwt_issuer` (that
combination makes the compose generator auto-provision Keycloak), embedding
provider `ollama` pointing at your Ollama host, and writes the four artifacts
to this directory. Secrets come from env vars (`GEN_API_KEY`,
`GEN_PG_PASSWORD`, `GEN_AUTH_SECRET`, `GEN_ERMYA_CLIENT_SECRET`,
`GEN_ADMIN_UI_CLIENT_SECRET`) or are randomized per run.

`ermya_config.json` is built via `build_example_config` with the same
Keycloak host/port the realm uses; embedding dimension must match the model
(e.g. `bge-m3` = 1024).

## 2. Known deltas vs. the generated output (as of 2026-07-22)

- **Image**: the generator emits `ermyaio/ermya:latest`; for local debug
  override it to a local image (e.g. `ermya:v0.53.16`).
- **`ERMYA_AUTH_BOOTSTRAP_PRINCIPAL_ULID` is missing from the generated
  `.env`** and Ermya ≥ v0.50 refuses to start without it (fail-closed
  AuthEngine bootstrap). Append it with any ULID before `docker compose up`.
  This is a Launchpad generator gap, pending fix in `config/env.rs`.
- **`vls.client_secret` is missing from `ermya_config.json`**: the realm's
  `ermya-client` is a confidential client, so the OAuth password grant
  requires `client_secret`; without it Keycloak answers `unauthorized_client`.
  Pending fix in the example (`config_loader.py`/`vls.py`) and in Launchpad
  (`example_config.rs`).

## 3. Run

```bash
docker compose up -d          # postgres + keycloak (imports realm) + ermya
# wait until `docker ps` shows all three healthy (keycloak takes ~1 min)
cp ermya_config.json ../python/ermya_config.json
cd ../python && .venv/bin/python main.py
```

Embeddings are external to the stack (same as Launchpad's compose): point
`embedding.endpoint` at a reachable Ollama with an embedding model pulled.
