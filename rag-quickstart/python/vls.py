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
