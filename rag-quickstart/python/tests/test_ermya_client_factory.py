"""Tests for the Ermya client factory: endpoint composition + construction."""

import ermya_client_factory
from config_loader import ErmyaConfig


def test_compose_endpoint_combines_host_and_port():
    assert (
        ermya_client_factory.compose_endpoint(host="localhost", port=50051)
        == "localhost:50051"
    )


def test_create_client_passes_correct_args(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, host, api_key, secure):
            captured["host"] = host
            captured["api_key"] = api_key
            captured["secure"] = secure

    monkeypatch.setattr(ermya_client_factory, "ErmyaClient", FakeClient)
    cfg = ErmyaConfig(host="myhost", port=9000, api_key="key123", secure=True)
    ermya_client_factory.create_client(cfg)
    assert captured == {"host": "myhost:9000", "api_key": "key123", "secure": True}
