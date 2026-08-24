"""Construct the Ermya SDK client from config.

The Python SDK takes a combined ``host:port`` string and a separate ``secure``
flag (unlike the TS/.NET SDKs, which take a scheme-prefixed URL).
"""

from __future__ import annotations

from ermya import ErmyaClient

from config_loader import ErmyaConfig


def compose_endpoint(host: str, port: int) -> str:
    """Combine host and port into the ``host:port`` form the SDK expects."""
    return f"{host}:{port}"


def create_client(config: ErmyaConfig) -> ErmyaClient:
    """Build a ErmyaClient from the connection config."""
    return ErmyaClient(
        host=compose_endpoint(config.host, config.port),
        api_key=config.api_key,
        secure=config.secure,
    )
