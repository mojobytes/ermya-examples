"""Construct the Tessera SDK client from config.

The Python SDK takes a combined ``host:port`` string and a separate ``secure``
flag (unlike the TS/.NET SDKs, which take a scheme-prefixed URL).
"""

from __future__ import annotations

from tessera import TesseraClient

from config_loader import TesseraConfig


def compose_endpoint(host: str, port: int) -> str:
    """Combine host and port into the ``host:port`` form the SDK expects."""
    return f"{host}:{port}"


def create_client(config: TesseraConfig) -> TesseraClient:
    """Build a TesseraClient from the connection config."""
    return TesseraClient(
        host=compose_endpoint(config.host, config.port),
        api_key=config.api_key,
        secure=config.secure,
    )
