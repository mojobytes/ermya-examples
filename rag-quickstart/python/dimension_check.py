"""Fail-fast verification that the provider returns vectors of the configured
dimension. The config is the source of truth; the example verifies reality
matches it (important for Ollama and custom models the launchpad cannot map)."""

from __future__ import annotations


def verify_dimension(vector: list[float], expected: int) -> None:
    """Raise ValueError if ``len(vector) != expected``, naming both values."""
    actual = len(vector)
    if actual != expected:
        raise ValueError(
            f"Dimension mismatch: the embedding provider returned a vector of "
            f"length {actual}, but ermya_config.json declares "
            f"embedding.dimension = {expected}. Update embedding.dimension to "
            f"match the model's output size, or pick a matching model."
        )
