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
