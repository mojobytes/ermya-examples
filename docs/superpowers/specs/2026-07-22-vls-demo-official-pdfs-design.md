# Design — VLS Demo with Official AI-Governance PDFs

**Date:** 2026-07-22
**Repos touched:** `ermya-examples` (the demo), `ermya-launchpad` (deploy + config), `ermya-python` (SDK — already complete, no changes)
**Roadmap:** Phase 3 of the go-to-market plan — make the generated example demonstrate the SDK's flagship differentiator (Vector-Level Security) on complex, real documents.

## Context

The launchpad-generated Python example (`ermya-examples/rag-quickstart/python`)
today does only `create_tenant + insert + search` on vector-only search. That
demonstrates nothing a generic vector DB cannot do. The SDK now exposes
Vector-Level Security (VLS): permission-aware search where the same query
returns different results per end user. This demo rewires the example to show
VLS on a corpus of **complex official AI-governance documents (PDFs)**, so a
prospect sees permission-filtered RAG over hard, real-world documents.

Scope decisions (fixed by the user during brainstorming):
- Differentiator shown: **VLS only** (hybrid/multi-db are separate future demos).
- Example stays in `ermya-examples`; launchpad **clones + configures** it
  (unchanged deployment pattern).
- User tokens are **real Keycloak JWTs** obtained via OAuth password grant
  against the Keycloak that launchpad deploys (Option A — realistic).
- Documents are **full official PDFs** (not extracts); the point is ingesting
  *structurally complex* documents.
- PDF text extraction uses **oxidize-pdf** (PyPI `oxidize-pdf` ≥0.15.1,
  `PdfReader.open().extract_text()`).

## Architecture (3 repos, 3 responsibilities)

```
ermya-launchpad          ermya-examples                 Ermya server (v0.53.x)
(deploy + configure)       (the runnable demo)              (VLS, no changes)
────────────────────       ─────────────────────            ────────────────────────
1. Keycloak realm seeds    3. pipeline:                     5. validates x-user-token
   Alice + Bob (with          - register principals            against Keycloak
   passwords)                 - extract PDFs (oxidize)         (signature/exp/issuer)
2. writes ermya_config    - ingest w/ per-doc ACLs        6. filters search results
   .json (+ VLS block:        - OAuth login Alice/Bob          by that user's grants
   issuer, client_id,         - same query, 2 tokens
   demo user creds)           - print disjoint results
```

**End-to-end flow:** launchpad deploys the stack (Ermya + Keycloak with Alice
& Bob) and generates the Python project with its config → user runs
`python main.py` → pipeline ingests the 11 PDFs with per-document ACLs, obtains
Alice's and Bob's JWTs from Keycloak, runs the **same** query with each token,
and prints that Alice and Bob get **disjoint** result sets.

## Components

### ermya-examples (the demo)

**`pdf_extractor.py`** (new) — the "tractor". `extract_text(path) -> str` using
`oxidize_pdf.PdfReader.open(path).extract_text()`. One function, injectable, so
tests can substitute a fake extractor. Replaces `parse_markdown_files` as the
document source; the existing `chunk_text` chunker consumes the extracted text
unchanged.

**`data/*.pdf`** (new) — the 11 official documents (table below), **committed to
the repo** so the example runs fully offline (the repo's README promises it runs
with no network). A `data/SOURCES.md` records each document's official source URL
and retrieval date for provenance. Repo-size increase from the PDFs is accepted.

**`vls.py`** (new) — VLS helpers, all injectable:
- `register_demo_principals(client, tenant_id) -> dict[str, str]` — registers
  Alice and Bob via `client.register_principal`, returns their principal IDs.
- `fetch_user_token(oidc_config, username, password) -> str` — OAuth2 password
  grant against Keycloak's token endpoint (via `requests`, already the example's
  HTTP client for embedding providers, with `requests-mock` available for
  tests), returns the access token JWT. Isolated so tests mock the HTTP.

**`pipeline.py`** (rewritten `run_pipeline`):
1. `create_tenant`.
2. `register_demo_principals`.
3. For each PDF: `extract_text` → `chunk_text` → `provider.embed` →
   `client.insert(..., permissions=[Permission(principal=<owner>, action="read")])`
   where `<owner>` is Alice or Bob per the ACL table.
4. `fetch_user_token` for Alice and for Bob.
5. Run the **same** demo query embedding with `user_token=alice_jwt`, then
   `user_token=bob_jwt`.
6. Print the two disjoint result sets side by side.

### Documents & ACL table

| # | Document | Jurisdiction | Owner |
|---|---|---|---|
| 1 | EU AI Act (Reg. 2024/1689) | 🇪🇺 EU | Alice |
| 5 | UK pro-innovation white paper | 🇬🇧 UK | Alice |
| 6 | UNESCO Ethics of AI Recommendation | 🌐 UNESCO | Alice |
| 7 | OECD Recommendation on AI (LEGAL/0449) | 🌐 OECD | Alice |
| 10 | Council of Europe Framework Convention (CETS 225) | 🌐 CoE | Alice |
| 2 | NIST AI RMF 1.0 (AI 100-1) | 🇺🇸 US | Bob |
| 3 | Australia AI Ethics Principles | 🇦🇺 AU | Bob |
| 4 | Canada Directive on Automated Decision-Making | 🇨🇦 CA | Bob |
| 8 | Singapore Model AI Gov. Framework (GenAI) | 🇸🇬 SG | Bob |
| 9 | Japan AI Guidelines for Business | 🇯🇵 JP | Bob |
| 11 | South Korea AI Basic / Framework Act | 🇰🇷 KR | Bob |

Alice = Europe + international bodies (5 docs). Bob = Americas + Asia-Pacific
(6 docs). **No document is shared**, so the same query returns disjoint sets —
the filtering is unambiguously visible.

Sources (official, primary where available):
- EU AI Act: https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689
- NIST AI RMF 1.0: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- Australia: https://www.industry.gov.au/publications/australias-ai-ethics-principles
- Canada: https://publications.gc.ca/collections/collection_2021/sct-tbs/BT48-31-2021-eng.pdf
- UK: https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach/white-paper
- UNESCO: https://unesdoc.unesco.org/ark:/48223/pf0000381137
- OECD: https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0449
- Singapore: https://aiverifyfoundation.sg/downloads/Proposed_MGF_Gen_AI_2024.pdf
- Japan: https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20240419_9.pdf
- Council of Europe: https://rm.coe.int/1680afae3c
- South Korea (English translation, CSET/Georgetown): https://aibasicact.kr/

### ermya-launchpad (deploy + config)

**`realm.rs`** — extend the existing `"users"` array (currently just `admin`)
to also seed `alice` and `bob` with known demo passwords, both able to obtain
tokens from the `ermya-client` OIDC client that the realm already declares.

**`example_config.rs`** / `ermya_config.json` — add a `vls` block:
`{ issuer, token_endpoint, client_id, alice: {username, password},
bob: {username, password} }`. The generated example reads it to run the OAuth
password grant. Marked clearly as demo-only plaintext (consistent with the
example's existing `_warning` banner).

### Ermya server

No changes. It already validates `x-user-token` (signature/expiry/issuer via
Keycloak) and filters results by the caller's grants.

## Error handling

- **PDF extraction failure** (corrupt/unreadable PDF): `pdf_extractor` raises a
  clear `PdfExtractionError` naming the file; the pipeline reports which
  document failed and continues with the rest (one bad PDF must not abort the
  whole demo), printing a summary of skipped documents at the end.
- **Missing `oxidize-pdf`**: import guarded with an actionable message
  (`pip install oxidize-pdf`) rather than a raw ImportError.
- **Keycloak token fetch failure** (Keycloak not ready, wrong creds): surface a
  clear message pointing at the deployed Keycloak URL and the demo creds in
  `ermya_config.json`; do not print the token.
- **VLS not configured** (no `vls` block in config, i.e. run outside launchpad):
  fall back to the current behaviour — ingest without ACLs and run a single
  vector search — so the example still runs standalone. The VLS demo section is
  skipped with a one-line notice. This preserves the "runnable on its own"
  property the repo README promises.
- **Tokens never logged**: Alice/Bob JWTs are used to build the metadata header
  only; never printed, never included in error messages.

## Testing strategy

Consistent with the repo's existing pattern (one test module per source module,
fully mocked, no live server or network — `-m 'not integration'` default):

- `test_pdf_extractor.py`: fake PDF path → asserts `extract_text` delegates to
  the (mocked) `PdfReader`; `PdfExtractionError` on a reader that raises.
- `test_vls.py`: `register_demo_principals` calls `register_principal` for both
  users; `fetch_user_token` posts the right OAuth password-grant body to the
  token endpoint (via `requests-mock`) and returns the access token; asserts the
  token never appears in printed/logged output.
- `test_pipeline.py` (extend): with a mocked client+provider+extractor, assert
  each document is inserted with the **correct owner** in its `permissions`, and
  that the demo runs the same query with each user's token; assert the printed
  result sets are disjoint given a mocked server that filters by owner.
- `test_pipeline.py` fallback: with no `vls` config, assert the pipeline ingests
  without ACLs and runs a single search (backward-compatible path).
- Integration test (marked `integration`, skipped by default): full run against
  a live launchpad-deployed stack — real Keycloak tokens, real VLS filtering.
  This is the only test needing the deployed stack; it documents the true
  end-to-end contract without gating the default suite.

## Out of scope

- Hybrid and multi-db demos (separate future examples).
- Moving the example into launchpad (rejected — clone pattern kept).
- Publishing images / the SDK to registries (Phase 4).
- A UI for the demo (it is a CLI quickstart).

## Verification (end-to-end)

1. On a clean machine, launchpad deploys the stack and generates the Python
   project with a `ermya_config.json` carrying the `vls` block.
2. `pip install` the example's deps (incl. `oxidize-pdf`, `ermya-vector`).
3. `python main.py` ingests the 11 PDFs with per-document ACLs.
4. The demo prints Alice's results (EU/UK/UNESCO/OECD/CoE fragments) and Bob's
   (NIST/AU/CA/SG/JP/KR fragments) for the **same** query — disjoint sets.
5. Unit suite green with the new modules; integration test green against the
   live stack.
