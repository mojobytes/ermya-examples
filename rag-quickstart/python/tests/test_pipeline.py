"""Tests for the orchestration pipeline.

The Tessera client and embedding provider are injected, so the whole flow is
exercised with mocks — no live Tessera, no real HTTP.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from config_loader import (
    Config,
    EmbeddingConfig,
    IngestionConfig,
    TesseraConfig,
)
from pipeline import run_pipeline


def make_config(dimension=4, tenant_id="rag-quickstart", chunk_size=10, chunk_overlap=0):
    return Config(
        tessera=TesseraConfig(host="localhost", port=50051, api_key="k", secure=False),
        embedding=EmbeddingConfig(
            provider="ollama",
            endpoint="http://localhost:11434",
            api_key="",
            model="nomic-embed-text",
            deployment_name="",
            dimension=dimension,
        ),
        ingestion=IngestionConfig(
            tenant_id=tenant_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            data_dir="./data",
        ),
    )


@pytest.fixture
def data_dir(tmp_path):
    # 20 chars -> with chunk_size=10, overlap=0 => exactly 2 chunks.
    (tmp_path / "doc.md").write_text("abcdefghijABCDEFGHIJ")
    return tmp_path


@pytest.fixture
def client():
    c = MagicMock()
    c.insert.return_value = 1
    c.search.return_value = []
    return c


@pytest.fixture
def provider():
    p = MagicMock()
    p.embed.return_value = [0.5, 0.5, 0.5, 0.5]  # dimension 4
    return p


def test_pipeline_prints_plaintext_banner(capsys, client, provider, data_dir):
    run_pipeline(make_config(), client, provider, data_dir)
    out = capsys.readouterr().out
    assert "QUICKSTART" in out.upper() or "EXAMPLE" in out.upper()
    assert "plaintext" in out.lower() or "not production" in out.lower()


def test_pipeline_creates_tenant_with_config_dimension(client, provider, data_dir):
    run_pipeline(make_config(dimension=4, tenant_id="my-tenant"), client, provider, data_dir)
    client.create_tenant.assert_called_once_with("my-tenant", 4)


def test_pipeline_embeds_each_chunk(client, provider, data_dir):
    run_pipeline(make_config(chunk_size=10, chunk_overlap=0), client, provider, data_dir)
    assert provider.embed.call_count == 2


def test_pipeline_verifies_dimension_after_first_embed(client, provider, data_dir):
    provider.embed.return_value = [0.1] * 384  # wrong dimension
    with pytest.raises(ValueError, match="Dimension mismatch"):
        run_pipeline(make_config(dimension=1536), client, provider, data_dir)
    # must fail fast, before inserting anything
    client.insert.assert_not_called()


def test_pipeline_inserts_each_chunk_with_metadata(client, provider, data_dir):
    run_pipeline(make_config(dimension=4, tenant_id="t1"), client, provider, data_dir)
    assert client.insert.call_count == 2
    for call in client.insert.call_args_list:
        args, kwargs = call
        tenant = kwargs.get("tenant_id", args[0] if args else None)
        vector = kwargs.get("vector", args[1] if len(args) > 1 else None)
        metadata = kwargs.get("metadata", args[2] if len(args) > 2 else None)
        assert tenant == "t1"
        assert len(vector) == 4
        assert "text" in metadata
        assert "source" in metadata


def test_pipeline_runs_demo_search(client, provider, data_dir):
    run_pipeline(make_config(dimension=4), client, provider, data_dir)
    assert client.search.called


def test_pipeline_no_documents_does_not_insert(client, provider, tmp_path):
    # empty data dir -> no chunks -> no embeds/inserts, but should not crash
    run_pipeline(make_config(), client, provider, tmp_path)
    provider.embed.assert_not_called()
    client.insert.assert_not_called()


# --- VLS pipeline tests (Task A5) ---

from config_loader import VlsConfig, VlsUser  # noqa: E402
from documents import ALICE, BOB  # noqa: E402
import pipeline as pipeline_mod  # noqa: E402


def _base_config(vls):
    return Config(
        tessera=TesseraConfig("h", 1, "", False),
        embedding=EmbeddingConfig("ollama", "e", "", "m", "", 3),
        ingestion=IngestionConfig("t1", 10, 0, "./data"),
        vls=vls,
    )


def _vls():
    return VlsConfig(
        issuer="iss", token_endpoint="te", client_id="tessera-client",
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


def test_vls_pipeline_never_prints_user_token(capsys):
    """Regression: ensure user tokens are never leaked to stdout.

    Tokens are fetched per-user and passed to client.search, but must never
    appear in any printed output. This test verifies the invariant by using
    a recognizable sentinel token and asserting it does not appear in stdout.
    """
    SENTINEL_TOKEN = "SECRET-TOKEN-abc123xyz"

    client = MagicMock()
    client.register_principal.side_effect = ["pid-a", "pid-b"]
    provider = MagicMock()
    provider.embed.return_value = [0.1, 0.2, 0.3]
    client.search.return_value = []

    # fetch_token returns the sentinel for each user
    def fake_fetch(vls, owner):
        if owner == ALICE:
            return SENTINEL_TOKEN
        return f"{SENTINEL_TOKEN}-{owner}"

    pipeline_mod.run_pipeline(
        _base_config(_vls()), client, provider, Path("./data"),
        extract=MagicMock(return_value="text"),
        fetch_token=fake_fetch,
    )

    # Verify the sentinel was actually passed to client.search
    user_tokens = {c.kwargs.get("user_token") for c in client.search.call_args_list}
    assert SENTINEL_TOKEN in user_tokens, "Test setup error: sentinel not passed to search"

    # Assert the token NEVER appears in stdout
    out = capsys.readouterr().out
    assert SENTINEL_TOKEN not in out, (
        f"Security regression: sentinel token leaked to stdout. "
        f"Output:\n{out}"
    )
