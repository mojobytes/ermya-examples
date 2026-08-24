# VLS Demo on Official AI-Governance PDFs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewire `ermya-examples/rag-quickstart/python` to demonstrate Vector-Level Security by ingesting 11 official AI-governance PDFs with per-document ACLs and running the same query as two different users (Alice, Bob) so results come back disjoint; and have `ermya-launchpad` seed those two users in Keycloak and write the VLS config block.

**Architecture:** The example gains a PDF extractor (oxidize-pdf), a VLS helper module (principal registration + OAuth token fetch), and a rewritten pipeline that inserts each document with an owner ACL then searches with each user's real Keycloak JWT. Config gains an optional `vls` block; when absent the example falls back to the current vector-only behaviour so it still runs standalone. Launchpad seeds Alice/Bob in the generated realm and writes the `vls` block into `ermya_config.json`.

**Tech Stack:** Python 3.10+, `ermya-vector` SDK, `oxidize-pdf` (PDF text), `requests` + `requests-mock` (OAuth), pytest. Rust (Tauri) for launchpad realm/config generation.

## Global Constraints

- Schema: `ermya_config.json` uses `schema_version: 1` (`config_loader.py:16`). The `vls` block is additive and optional; absence must not break loading.
- The example MUST run offline with no live server/network for the default test suite (`-m 'not integration'`); PDFs are committed to the repo.
- Dependency injection: `run_pipeline(config, client, provider, data_dir)` receives its collaborators; new collaborators (PDF extractor) are injected too, so tests never touch a real server, real HTTP, or a real PDF engine.
- User JWTs (Alice/Bob tokens) MUST NEVER be printed or included in any log/error message.
- SDK signatures (verified): `Permission(principal: str, action: str)`; `client.register_principal(tenant_id: str, external_id: str, external_kind: str = "user") -> str` (returns principal ULID); `client.insert(tenant_id, vector, metadata=None, permissions: list[Permission] | None = None, database_id="")`; `client.search(tenant_id, vector, k=10, ..., user_token: str | None = None)`.
- Example config types (verified, `config_loader.py`): dataclasses `ErmyaConfig(host, port, api_key, secure)`, `EmbeddingConfig(provider, endpoint, api_key, model, deployment_name, dimension)`, `IngestionConfig(tenant_id, chunk_size, chunk_overlap, data_dir)`, `Config(ermya, embedding, ingestion)`.
- `chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]` (verified, `chunker.py`).

---

# PART A — ermya-examples (the runnable demo)

Work in `/Volumes/WD_BLACK/repos/MojoBytes/ermya-ecosystem/ermya-examples/rag-quickstart/python`. Repo branch: `development`. Run pytest from that directory with its `.venv` (create one if absent: `python -m venv .venv && .venv/bin/pip install -e '.[test]'` plus `oxidize-pdf`).

## Task A1: PDF extractor

**Files:**
- Create: `rag-quickstart/python/pdf_extractor.py`
- Test: `rag-quickstart/python/tests/test_pdf_extractor.py`
- Modify: `rag-quickstart/python/pyproject.toml` (add `oxidize-pdf>=0.15.1` to deps), `rag-quickstart/python/requirements.txt`

**Interfaces:**
- Produces: `extract_text(path: str | Path, *, reader=None) -> str` — extracts all text from a PDF; `reader` is an injectable factory defaulting to `oxidize_pdf.PdfReader.open` so tests substitute a fake. Raises `PdfExtractionError(path, cause)` on failure.
- Produces: `class PdfExtractionError(Exception)` with attribute `.path`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pdf_extractor.py
from unittest.mock import MagicMock
import pytest
from pdf_extractor import extract_text, PdfExtractionError


def test_extract_text_delegates_to_reader():
    fake_doc = MagicMock()
    fake_doc.extract_text.return_value = "EU AI Act Article 1 ..."
    fake_reader = MagicMock(return_value=fake_doc)

    text = extract_text("data/eu_ai_act.pdf", reader=fake_reader)

    fake_reader.assert_called_once_with("data/eu_ai_act.pdf")
    assert text == "EU AI Act Article 1 ..."


def test_extract_text_wraps_reader_failure():
    def boom(_path):
        raise RuntimeError("corrupt xref")
    with pytest.raises(PdfExtractionError) as exc:
        extract_text("data/broken.pdf", reader=boom)
    assert exc.value.path == "data/broken.pdf"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_pdf_extractor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pdf_extractor'`.

- [ ] **Step 3: Write minimal implementation**

```python
# pdf_extractor.py
"""Extract text from PDF documents via oxidize-pdf.

The reader is injectable so tests never open a real PDF. main() uses the real
oxidize_pdf.PdfReader.open.
"""
from __future__ import annotations

from pathlib import Path


class PdfExtractionError(Exception):
    """Raised when a PDF cannot be read/extracted."""

    def __init__(self, path: str, cause: Exception):
        super().__init__(f"failed to extract text from {path}: {cause}")
        self.path = path
        self.cause = cause


def _default_reader(path):
    from oxidize_pdf import PdfReader  # imported lazily for a clear error

    return PdfReader.open(path)


def extract_text(path: str | Path, *, reader=None) -> str:
    """Extract all text from the PDF at ``path``."""
    reader = reader or _default_reader
    key = str(path)
    try:
        document = reader(key)
        return document.extract_text()
    except Exception as cause:  # noqa: BLE001 — wrap any engine error
        raise PdfExtractionError(key, cause) from cause
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_pdf_extractor.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Add the dependency**

In `pyproject.toml` `[project].dependencies`, add `"oxidize-pdf>=0.15.1"`. In `requirements.txt`, add `oxidize-pdf>=0.15.1`.

- [ ] **Step 6: Commit**

```bash
git add rag-quickstart/python/pdf_extractor.py rag-quickstart/python/tests/test_pdf_extractor.py rag-quickstart/python/pyproject.toml rag-quickstart/python/requirements.txt
git commit -m "feat(examples): PDF text extractor via oxidize-pdf"
```

## Task A2: Document catalog + ACL table

**Files:**
- Create: `rag-quickstart/python/documents.py`
- Test: `rag-quickstart/python/tests/test_documents.py`

**Interfaces:**
- Produces: `ALICE = "alice"`, `BOB = "bob"` (owner constants).
- Produces: `@dataclass(frozen=True) class Document: filename: str; jurisdiction: str; owner: str`.
- Produces: `DOCUMENTS: list[Document]` — the 11 entries from the spec's ACL table.
- Produces: `owners() -> set[str]` → `{"alice", "bob"}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_documents.py
from documents import DOCUMENTS, Document, ALICE, BOB, owners


def test_has_eleven_documents():
    assert len(DOCUMENTS) == 11
    assert all(isinstance(d, Document) for d in DOCUMENTS)


def test_ownership_split_is_disjoint_5_and_6():
    alice_docs = [d for d in DOCUMENTS if d.owner == ALICE]
    bob_docs = [d for d in DOCUMENTS if d.owner == BOB]
    assert len(alice_docs) == 5
    assert len(bob_docs) == 6
    # every doc owned by exactly one of the two
    assert {d.owner for d in DOCUMENTS} == {ALICE, BOB}


def test_filenames_unique():
    names = [d.filename for d in DOCUMENTS]
    assert len(names) == len(set(names))


def test_owners_helper():
    assert owners() == {ALICE, BOB}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_documents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'documents'`.

- [ ] **Step 3: Write minimal implementation**

```python
# documents.py
"""The demo corpus: 11 official AI-governance PDFs with per-document ACLs.

Alice = Europe + international bodies; Bob = Americas + Asia-Pacific. No document
is shared, so the same query returns disjoint sets per user.
"""
from __future__ import annotations

from dataclasses import dataclass

ALICE = "alice"
BOB = "bob"


@dataclass(frozen=True)
class Document:
    filename: str
    jurisdiction: str
    owner: str


DOCUMENTS: list[Document] = [
    Document("eu_ai_act.pdf", "EU", ALICE),
    Document("uk_pro_innovation_white_paper.pdf", "UK", ALICE),
    Document("unesco_ethics_of_ai.pdf", "UNESCO", ALICE),
    Document("oecd_recommendation_ai.pdf", "OECD", ALICE),
    Document("council_of_europe_framework_convention.pdf", "CoE", ALICE),
    Document("nist_ai_rmf_1_0.pdf", "US", BOB),
    Document("australia_ai_ethics_principles.pdf", "AU", BOB),
    Document("canada_directive_automated_decision_making.pdf", "CA", BOB),
    Document("singapore_model_ai_governance_genai.pdf", "SG", BOB),
    Document("japan_ai_guidelines_for_business.pdf", "JP", BOB),
    Document("south_korea_ai_basic_act.pdf", "KR", BOB),
]


def owners() -> set[str]:
    return {d.owner for d in DOCUMENTS}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_documents.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add rag-quickstart/python/documents.py rag-quickstart/python/tests/test_documents.py
git commit -m "feat(examples): document catalog with per-document ACL owners"
```

## Task A3: VLS config block in config_loader

**Files:**
- Modify: `rag-quickstart/python/config_loader.py`
- Test: `rag-quickstart/python/tests/test_config_loader.py` (extend)

**Interfaces:**
- Produces: `@dataclass class VlsUser: username: str; password: str`.
- Produces: `@dataclass class VlsConfig: issuer: str; token_endpoint: str; client_id: str; users: dict[str, VlsUser]` where keys are owner ids (`"alice"`, `"bob"`).
- Produces: `Config` gains `vls: VlsConfig | None = None` (defaults to `None` so existing configs and `_default_config()` are unchanged).
- Consumes: reads an optional top-level `"vls"` object from `ermya_config.json`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config_loader.py (append)
def test_load_config_reads_vls_block(tmp_path):
    (tmp_path / "ermya_config.json").write_text(json.dumps({
        "schema_version": 1,
        "ermya": {"host": "h", "port": 1, "api_key": "", "secure": False},
        "embedding": {"provider": "ollama", "endpoint": "e", "api_key": "",
                      "model": "m", "deployment_name": "", "dimension": 3},
        "ingestion": {"tenant_id": "t", "chunk_size": 1, "chunk_overlap": 0,
                      "data_dir": "./data"},
        "vls": {
            "issuer": "http://kc/realms/ermya",
            "token_endpoint": "http://kc/realms/ermya/protocol/openid-connect/token",
            "client_id": "ermya-client",
            "users": {
                "alice": {"username": "alice", "password": "pw-a"},
                "bob": {"username": "bob", "password": "pw-b"},
            },
        },
    }))
    from config_loader import load_config
    cfg = load_config(tmp_path)
    assert cfg.vls is not None
    assert cfg.vls.client_id == "ermya-client"
    assert cfg.vls.users["alice"].password == "pw-a"


def test_load_config_without_vls_leaves_it_none(tmp_path):
    (tmp_path / "ermya_config.json").write_text(json.dumps({
        "schema_version": 1,
        "ermya": {"host": "h", "port": 1, "api_key": "", "secure": False},
        "embedding": {"provider": "ollama", "endpoint": "e", "api_key": "",
                      "model": "m", "deployment_name": "", "dimension": 3},
        "ingestion": {"tenant_id": "t", "chunk_size": 1, "chunk_overlap": 0,
                      "data_dir": "./data"},
    }))
    from config_loader import load_config
    assert load_config(tmp_path).vls is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_config_loader.py -k vls -v`
Expected: FAIL — `AttributeError: 'Config' object has no attribute 'vls'`.

- [ ] **Step 3: Write minimal implementation**

In `config_loader.py`, add the dataclasses after `IngestionConfig`:

```python
@dataclass
class VlsUser:
    username: str
    password: str


@dataclass
class VlsConfig:
    issuer: str
    token_endpoint: str
    client_id: str
    users: dict[str, VlsUser]
```

Add `vls: VlsConfig | None = None` as the last field of `Config`. In `_parse_config`, after building ermya/embedding/ingestion, parse the optional block:

```python
    vls = None
    vls_raw = data.get("vls")
    if vls_raw is not None:
        vls = VlsConfig(
            issuer=vls_raw["issuer"],
            token_endpoint=vls_raw["token_endpoint"],
            client_id=vls_raw["client_id"],
            users={
                owner: VlsUser(username=u["username"], password=u["password"])
                for owner, u in vls_raw["users"].items()
            },
        )
    return Config(ermya=ermya, embedding=embedding, ingestion=ingestion, vls=vls)
```

(Adjust the final `return` to match the existing one, adding `vls=vls`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_config_loader.py -v`
Expected: PASS (existing tests + 2 new).

- [ ] **Step 5: Commit**

```bash
git add rag-quickstart/python/config_loader.py rag-quickstart/python/tests/test_config_loader.py
git commit -m "feat(examples): optional VLS config block (issuer, client, demo users)"
```

## Task A4: VLS helpers (principals + token fetch)

**Files:**
- Create: `rag-quickstart/python/vls.py`
- Test: `rag-quickstart/python/tests/test_vls.py`

**Interfaces:**
- Consumes: `VlsConfig`, `VlsUser` from `config_loader`; `DOCUMENTS`, `ALICE`, `BOB` from `documents`.
- Produces: `register_demo_principals(client, tenant_id: str) -> dict[str, str]` — calls `client.register_principal(tenant_id, external_id=owner, external_kind="user")` for each owner in `owners()`, returns `{owner: principal_id}`.
- Produces: `fetch_user_token(vls: VlsConfig, owner: str, *, session=None) -> str` — OAuth2 password grant POST to `vls.token_endpoint` with `grant_type=password`, `client_id=vls.client_id`, `username`/`password` from `vls.users[owner]`; returns `access_token`. `session` defaults to the `requests` module so `requests-mock` works.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_vls.py
from unittest.mock import MagicMock
import requests_mock

from config_loader import VlsConfig, VlsUser
from documents import ALICE, BOB
from vls import register_demo_principals, fetch_user_token


def _vls_config():
    return VlsConfig(
        issuer="http://kc/realms/ermya",
        token_endpoint="http://kc/realms/ermya/protocol/openid-connect/token",
        client_id="ermya-client",
        users={
            ALICE: VlsUser("alice", "pw-a"),
            BOB: VlsUser("bob", "pw-b"),
        },
    )


def test_register_demo_principals_registers_both():
    client = MagicMock()
    client.register_principal.side_effect = ["pid-alice", "pid-bob"]

    result = register_demo_principals(client, tenant_id="t1")

    assert set(result.keys()) == {ALICE, BOB}
    # each owner registered as a user principal in the tenant
    called_ids = {c.kwargs.get("external_id") or c.args[1]
                  for c in client.register_principal.call_args_list}
    assert called_ids == {ALICE, BOB}


def test_fetch_user_token_does_password_grant():
    vls = _vls_config()
    with requests_mock.Mocker() as m:
        m.post(vls.token_endpoint, json={"access_token": "jwt-alice"})
        token = fetch_user_token(vls, ALICE)
        assert token == "jwt-alice"
        body = m.last_request.text
        assert "grant_type=password" in body
        assert "client_id=ermya-client" in body
        assert "username=alice" in body


def test_fetch_user_token_never_returns_password_in_token():
    vls = _vls_config()
    with requests_mock.Mocker() as m:
        m.post(vls.token_endpoint, json={"access_token": "jwt-bob"})
        token = fetch_user_token(vls, BOB)
        assert "pw-b" not in token
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_vls.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vls'`.

- [ ] **Step 3: Write minimal implementation**

```python
# vls.py
"""VLS demo helpers: register demo principals and fetch their Keycloak tokens.

Tokens are used only to build the search metadata header; they are never
printed or logged.
"""
from __future__ import annotations

import requests

from config_loader import VlsConfig
from documents import owners


def register_demo_principals(client, tenant_id: str) -> dict[str, str]:
    """Register each demo owner as a user principal; return {owner: principal_id}."""
    result: dict[str, str] = {}
    for owner in sorted(owners()):
        result[owner] = client.register_principal(
            tenant_id, external_id=owner, external_kind="user"
        )
    return result


def fetch_user_token(vls: VlsConfig, owner: str, *, session=None) -> str:
    """OAuth2 password grant against Keycloak; return the access-token JWT."""
    session = session or requests
    user = vls.users[owner]
    response = session.post(
        vls.token_endpoint,
        data={
            "grant_type": "password",
            "client_id": vls.client_id,
            "username": user.username,
            "password": user.password,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_vls.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add rag-quickstart/python/vls.py rag-quickstart/python/tests/test_vls.py
git commit -m "feat(examples): VLS helpers — register principals + OAuth token fetch"
```

## Task A5: Rewire the pipeline (VLS ingest + dual-user search, with fallback)

**Files:**
- Modify: `rag-quickstart/python/pipeline.py`
- Test: `rag-quickstart/python/tests/test_pipeline.py` (extend)

**Interfaces:**
- Consumes: `extract_text` (A1), `DOCUMENTS`/`ALICE`/`BOB` (A2), `VlsConfig` (A3), `register_demo_principals`/`fetch_user_token` (A4), existing `chunk_text`, `Permission` from `ermya`.
- Produces: `run_pipeline(config, client, provider, data_dir, *, extract=extract_text, fetch_token=fetch_user_token)` — same public entry, with injectable `extract`/`fetch_token` for tests. When `config.vls` is set, runs the VLS demo; otherwise falls back to the current vector-only ingest+search.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pipeline.py (append)
from unittest.mock import MagicMock
from pathlib import Path
from config_loader import Config, ErmyaConfig, EmbeddingConfig, IngestionConfig, VlsConfig, VlsUser
from documents import ALICE, BOB
from ermya import Permission
import pipeline as pipeline_mod


def _base_config(vls):
    return Config(
        ermya=ErmyaConfig("h", 1, "", False),
        embedding=EmbeddingConfig("ollama", "e", "", "m", "", 3),
        ingestion=IngestionConfig("t1", 10, 0, "./data"),
        vls=vls,
    )


def _vls():
    return VlsConfig(
        issuer="iss", token_endpoint="te", client_id="ermya-client",
        users={ALICE: VlsUser("alice", "pw-a"), BOB: VlsUser("bob", "pw-b")},
    )


def test_vls_pipeline_inserts_each_doc_with_owner_acl():
    client = MagicMock()
    client.register_principal.side_effect = ["pid-a", "pid-b"]
    provider = MagicMock()
    provider.embed.return_value = [0.1, 0.2, 0.3]
    client.search.return_value = []

    fake_extract = MagicMock(return_value="Article 1 transparency ...")
    fake_fetch = MagicMock(side_effect=lambda vls, owner: f"jwt-{owner}")

    pipeline_mod.run_pipeline(
        _base_config(_vls()), client, provider, Path("./data"),
        extract=fake_extract, fetch_token=fake_fetch,
    )

    # Every insert carries a single-owner read permission
    owners_seen = set()
    for call in client.insert.call_args_list:
        perms = call.kwargs["permissions"]
        assert len(perms) == 1 and perms[0].action == "read"
        owners_seen.add(perms[0].principal)
    assert owners_seen == {ALICE, BOB}


def test_vls_pipeline_searches_once_per_user_token():
    client = MagicMock()
    client.register_principal.side_effect = ["pid-a", "pid-b"]
    provider = MagicMock()
    provider.embed.return_value = [0.1, 0.2, 0.3]
    client.search.return_value = []
    pipeline_mod.run_pipeline(
        _base_config(_vls()), client, provider, Path("./data"),
        extract=MagicMock(return_value="text"),
        fetch_token=MagicMock(side_effect=lambda vls, owner: f"jwt-{owner}"),
    )
    user_tokens = {c.kwargs.get("user_token") for c in client.search.call_args_list}
    assert user_tokens == {"jwt-alice", "jwt-bob"}


def test_fallback_without_vls_ingests_without_acls():
    client = MagicMock()
    provider = MagicMock()
    provider.embed.return_value = [0.1, 0.2, 0.3]
    client.search.return_value = []
    pipeline_mod.run_pipeline(
        _base_config(None), client, provider, Path("./data"),
        extract=MagicMock(return_value="text"),
        fetch_token=MagicMock(),
    )
    # no permissions passed, no per-user search
    for call in client.insert.call_args_list:
        assert not call.kwargs.get("permissions")
    for call in client.search.call_args_list:
        assert call.kwargs.get("user_token") is None
    client.register_principal.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_pipeline.py -k "vls or fallback" -v`
Expected: FAIL — `run_pipeline() got an unexpected keyword argument 'extract'`.

- [ ] **Step 3: Write minimal implementation**

Rewrite `pipeline.py`. Keep the banner and the standalone fallback. New shape:

```python
from documents import DOCUMENTS
from pdf_extractor import extract_text
from ermya import Permission
from vls import register_demo_principals, fetch_user_token

DEMO_QUERY = "transparency obligations for high-risk AI systems"


def run_pipeline(config, client, provider, data_dir, *,
                 extract=extract_text, fetch_token=fetch_user_token):
    print(BANNER)
    client.create_tenant(config.ingestion.tenant_id, config.embedding.dimension)

    if config.vls is not None:
        _run_vls_demo(config, client, provider, data_dir, extract, fetch_token)
    else:
        _run_standalone(config, client, provider, data_dir, extract)


def _ingest_pdf(client, provider, config, data_dir, doc, extract, permissions):
    text = extract(str(Path(data_dir) / doc.filename))
    chunks = chunk_text(text, config.ingestion.chunk_size, config.ingestion.chunk_overlap)
    first = None
    for i, chunk in enumerate(chunks):
        vector = provider.embed(chunk)
        if first is None:
            verify_dimension(vector, config.embedding.dimension)
            first = vector
        client.insert(
            tenant_id=config.ingestion.tenant_id, vector=vector,
            metadata={"text": chunk, "source": doc.filename, "chunk": i,
                      "jurisdiction": doc.jurisdiction},
            permissions=permissions,
        )
    return first


def _run_vls_demo(config, client, provider, data_dir, extract, fetch_token):
    register_demo_principals(client, config.ingestion.tenant_id)
    for doc in DOCUMENTS:
        perms = [Permission(principal=doc.owner, action="read")]
        _ingest_pdf(client, provider, config, data_dir, doc, extract, perms)

    query_vector = provider.embed(DEMO_QUERY)
    for owner in sorted(config.vls.users):
        token = fetch_token(config.vls, owner)
        results = client.search(
            tenant_id=config.ingestion.tenant_id, vector=query_vector,
            k=5, user_token=token,
        )
        _print_results(owner, results)  # NEVER print the token


def _run_standalone(config, client, provider, data_dir, extract):
    first = None
    for doc in DOCUMENTS:
        v = _ingest_pdf(client, provider, config, data_dir, doc, extract, None)
        first = first or v
    if first is None:
        print("No documents ingested.")
        return
    results = client.search(tenant_id=config.ingestion.tenant_id, vector=first, k=5)
    _print_results("(no VLS)", results)
```

Add `_print_results(label, results)` printing id/distance/jurisdiction (reuse the existing `_demo_search` formatting; it must not reference any token). Import `Path`, `chunk_text`, `verify_dimension` as the current file already does.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_pipeline.py -v`
Expected: PASS (existing + 3 new).

- [ ] **Step 5: Commit**

```bash
git add rag-quickstart/python/pipeline.py rag-quickstart/python/tests/test_pipeline.py
git commit -m "feat(examples): VLS pipeline — per-doc ACL ingest + dual-user search, standalone fallback"
```

## Task A6: Wire main() + PDFs + SOURCES.md

**Files:**
- Modify: `rag-quickstart/python/main.py`
- Create: `rag-quickstart/python/data/*.pdf` (11 files), `rag-quickstart/python/data/SOURCES.md`
- Modify: `rag-quickstart/python/README.md` (document the VLS demo + oxidize-pdf dep)
- Test: `rag-quickstart/python/tests/test_main.py` (extend, still mocked)

**Interfaces:**
- Consumes: everything above. `main()` already builds client+provider from config and calls `run_pipeline`; it needs no signature change (the injected defaults resolve to the real `extract_text`/`fetch_user_token`).

- [ ] **Step 1: Download the 11 PDFs into `data/`** using the filenames from `documents.py` (Task A2) and the source URLs in the spec's ACL table. Verify each file is a non-empty PDF: `file data/*.pdf` should report "PDF document" for all 11.

- [ ] **Step 2: Write `data/SOURCES.md`** — a table of `filename | jurisdiction | official source URL | retrieved date (2026-07-22)` for provenance, copied from the spec's sources list.

- [ ] **Step 3: Write the failing test** (main still runs fully mocked)

```python
# tests/test_main.py (append)
def test_main_runs_pipeline_with_config(monkeypatch, tmp_path):
    # main() must call run_pipeline exactly once with the loaded config;
    # patch create_client/create_provider/run_pipeline so nothing real runs.
    import main as main_mod
    called = {}
    monkeypatch.setattr(main_mod, "create_client", lambda c: MagicMock())
    monkeypatch.setattr(main_mod, "create_provider", lambda c: MagicMock())
    monkeypatch.setattr(main_mod, "run_pipeline",
                        lambda *a, **k: called.setdefault("ran", True))
    monkeypatch.chdir(tmp_path)  # no config → defaults, vls None
    main_mod.main()
    assert called["ran"] is True
```

- [ ] **Step 4: Run test to verify it fails (or passes if main already delegates)**

Run: `.venv/bin/python -m pytest tests/test_main.py -v`
Expected: If `main()` already delegates cleanly, this passes; if `main()` needs adjustment to import `run_pipeline` at module scope so it is patchable, make that minimal change and re-run.

- [ ] **Step 5: Update README** — add a "VLS demo" section: what it shows (Alice vs Bob disjoint results), the `oxidize-pdf` dependency, and that without a `vls` config block it runs standalone (vector-only).

- [ ] **Step 6: Run the full unit suite**

Run: `.venv/bin/python -m pytest -m "not integration" -v`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add rag-quickstart/python/main.py rag-quickstart/python/data rag-quickstart/python/README.md rag-quickstart/python/tests/test_main.py
git commit -m "feat(examples): wire main + commit official PDFs + SOURCES + README"
```

## Task A7: Integration test (marked, skipped by default)

**Files:**
- Create: `rag-quickstart/python/tests/test_integration_vls.py`

**Interfaces:**
- Consumes: a live launchpad-deployed stack (Ermya + Keycloak with Alice/Bob) and a real `ermya_config.json` with a `vls` block.

- [ ] **Step 1: Write the integration test**

```python
# tests/test_integration_vls.py
import pytest
from config_loader import load_config
from ermya_client_factory import create_client
from embedding import create_provider
from pipeline import run_pipeline
from pathlib import Path


@pytest.mark.integration
def test_vls_end_to_end_disjoint_results():
    """Requires a launchpad-deployed stack + ermya_config.json with a vls block.
    Ingests the 11 PDFs, then re-queries as each user and asserts the recovered
    jurisdictions are disjoint (Alice = EU/UK/UNESCO/OECD/CoE; Bob = the rest)."""
    from vls import fetch_user_token

    config = load_config(Path("."))
    assert config.vls is not None, "run this against a launchpad-generated config"
    client = create_client(config.ermya)
    provider = create_provider(config.embedding)

    # Ingest everything (this registers principals + inserts with ACLs).
    run_pipeline(config, client, provider, Path(config.ingestion.data_dir))

    # Re-query the SAME vector as each user and collect the jurisdictions they see.
    query_vector = provider.embed("transparency obligations for high-risk AI systems")
    seen: dict[str, set[str]] = {}
    for owner in sorted(config.vls.users):
        token = fetch_user_token(config.vls, owner)
        results = client.search(
            tenant_id=config.ingestion.tenant_id, vector=query_vector,
            k=20, user_token=token,
        )
        seen[owner] = {
            (r.metadata or {}).get("jurisdiction")
            for r in results if getattr(r, "metadata", None)
        }

    alice_j, bob_j = seen["alice"], seen["bob"]
    assert alice_j and bob_j, "each user must recover at least one document"
    assert alice_j.isdisjoint(bob_j), (
        f"VLS leak: Alice {alice_j} and Bob {bob_j} overlap"
    )
```

- [ ] **Step 2: Verify it is deselected by default**

Run: `.venv/bin/python -m pytest -m "not integration" -q`
Expected: the integration test is deselected (not collected).

- [ ] **Step 3: Commit**

```bash
git add rag-quickstart/python/tests/test_integration_vls.py
git commit -m "test(examples): integration test for end-to-end VLS (marked, skipped by default)"
```

---

# PART B — ermya-launchpad (seed Keycloak + write VLS config)

Work in `/Volumes/WD_BLACK/repos/MojoBytes/ermya-ecosystem/ermya-launchpad`. This lands on `feature/example-project-generator` (where the generator lives) — confirm the branch before starting; do NOT try to merge that branch into main here (that reconciliation is out of scope for this plan). Run Rust tests with `cargo test` in `src-tauri`.

## Task B1: Seed Alice and Bob in the Keycloak realm

**Files:**
- Modify: `src-tauri/src/config/realm.rs` (extend the `"users"` array that currently holds only `admin`)
- Test: `src-tauri/src/config/realm.rs` (extend the existing `#[cfg(test)]` module — it already asserts `users` contains `admin`)

**Interfaces:**
- Produces: the generated realm JSON `users` array additionally contains `alice` and `bob`, each with a set password credential and enabled, in the same realm as `admin`.

- [ ] **Step 1: Write the failing test** (extend the realm test module)

```rust
#[test]
fn realm_seeds_alice_and_bob_demo_users() {
    let json = generate_realm(&sample_input());
    let v: serde_json::Value = serde_json::from_str(&json).unwrap();
    let users = v["users"].as_array().unwrap();
    for name in ["alice", "bob"] {
        let u = users.iter().find(|u| u["username"] == name)
            .unwrap_or_else(|| panic!("missing demo user {name}"));
        assert_eq!(u["enabled"], true);
        let creds = u["credentials"].as_array().unwrap();
        assert!(creds.iter().any(|c| c["type"] == "password"));
    }
}
```

(Use the same `sample_input()` helper the existing realm tests use; if none, build a minimal `GenerateConfigInput` as the neighbouring tests do.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cargo test --manifest-path src-tauri/Cargo.toml realm_seeds_alice_and_bob -- --nocapture`
Expected: FAIL — demo user not found.

- [ ] **Step 3: Write minimal implementation**

In `realm.rs`, where the `users` array is built (currently emits `admin`), append two more user objects `alice` and `bob`, each `enabled: true` with a password credential (use fixed demo passwords, e.g. `alice`/`bob` or values from the input if the generator threads them). Mirror the exact JSON shape of the existing `admin` user entry.

- [ ] **Step 4: Run test to verify it passes**

Run: `cargo test --manifest-path src-tauri/Cargo.toml realm_seeds_alice_and_bob`
Expected: PASS. Also run the full realm test module to confirm no regression: `cargo test --manifest-path src-tauri/Cargo.toml realm`.

- [ ] **Step 5: Commit**

```bash
git add src-tauri/src/config/realm.rs
git commit -m "feat(launchpad): seed alice and bob demo users in the Keycloak realm"
```

## Task B2: Write the VLS block into ermya_config.json

**Files:**
- Modify: `src-tauri/src/config/example_config.rs` (the `ermya_config.json` builder)
- Test: `src-tauri/src/config/example_config.rs` (extend its test module)

**Interfaces:**
- Consumes: the deployed Keycloak issuer/token endpoint and `ermya-client` client id (already known to the realm generator); the demo user credentials from B1.
- Produces: the written `ermya_config.json` gains a top-level `"vls"` object matching the schema Part A Task A3 parses: `{issuer, token_endpoint, client_id, users: {alice: {username, password}, bob: {username, password}}}`.

- [ ] **Step 1: Write the failing test**

```rust
#[test]
fn config_includes_vls_block_for_demo_users() {
    let json = build_example_config(&sample_config_input());
    let v: serde_json::Value = serde_json::from_str(&json).unwrap();
    let vls = &v["vls"];
    assert_eq!(vls["client_id"], "ermya-client");
    assert!(vls["issuer"].is_string());
    assert!(vls["token_endpoint"].is_string());
    assert_eq!(vls["users"]["alice"]["username"], "alice");
    assert_eq!(vls["users"]["bob"]["username"], "bob");
}
```

(Use the example_config builder's existing test input helper.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cargo test --manifest-path src-tauri/Cargo.toml config_includes_vls_block`
Expected: FAIL — no `vls` key.

- [ ] **Step 3: Write minimal implementation**

In `example_config.rs`, add a `vls` object to the serialized config, derived from the same Keycloak host/port the realm uses (issuer `http://<kc-host>:<port>/realms/ermya`, token endpoint `.../protocol/openid-connect/token`), `client_id = "ermya-client"`, and the alice/bob usernames+passwords used in B1. Keep the plaintext-demo warning consistent with the existing `_warning` field.

- [ ] **Step 4: Run test to verify it passes**

Run: `cargo test --manifest-path src-tauri/Cargo.toml config_includes_vls_block`
Expected: PASS. Run the full example_config test module too.

- [ ] **Step 5: Commit**

```bash
git add src-tauri/src/config/example_config.rs
git commit -m "feat(launchpad): write VLS block (issuer, client, demo users) into ermya_config.json"
```

## Task B3: Backend test suite green

- [ ] **Step 1: Run the full Rust suite**

Run: `cargo test --manifest-path src-tauri/Cargo.toml`
Expected: all green (417+ backend tests plus the 2 new).

- [ ] **Step 2: Run the frontend suite** (unchanged, but confirm no break)

Run: `npm test` (from repo root)
Expected: green.

- [ ] **Step 3: No commit** (verification only; nothing changed).

---

## Verification (end-to-end, manual — after both parts land)

1. On a clean machine, launchpad (feature branch) deploys the stack and generates the Python project; `ermya_config.json` contains the `vls` block and Keycloak has alice/bob.
2. `pip install -e '.[test]'` + `pip install oxidize-pdf ermya-vector` in the generated project.
3. `python main.py` ingests the 11 PDFs with per-document ACLs, fetches Alice's and Bob's tokens, runs the same query with each, prints disjoint result sets (Alice: EU/UK/UNESCO/OECD/CoE; Bob: US/AU/CA/SG/JP/KR).
4. `pytest -m "not integration"` green in the example; `pytest -m integration` green against the live stack.
