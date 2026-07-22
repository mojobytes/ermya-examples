"""Integration test for end-to-end VLS demo with real Keycloak and launchpad stack.

This test requires a launchpad-deployed Tessera + Keycloak and a tessera_config.json
with a vls block. It is marked @pytest.mark.integration and is deselected by default
(run with -m integration to enable).

The test verifies that Alice and Bob have disjoint document jurisdictions after
ingesting the full corpus with per-document ACLs and re-querying as each user.
"""
import pytest
from config_loader import load_config
from tessera_client_factory import create_client
from embedding import create_provider
from pipeline import run_pipeline
from pathlib import Path


@pytest.mark.integration
def test_vls_end_to_end_disjoint_results():
    """Requires a launchpad-deployed stack + tessera_config.json with a vls block.
    Ingests the 11 PDFs, then re-queries as each user and asserts the recovered
    jurisdictions are disjoint (Alice = EU/UK/UNESCO/OECD/CoE; Bob = the rest)."""
    from vls import fetch_user_token

    config = load_config(Path("."))
    assert config.vls is not None, "run this against a launchpad-generated config"
    client = create_client(config.tessera)
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
