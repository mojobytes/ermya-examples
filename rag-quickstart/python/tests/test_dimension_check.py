"""Tests for dimension verification: config dimension must match the vector."""

import pytest

from dimension_check import verify_dimension


def test_dimension_check_passes_on_match():
    verify_dimension([0.1] * 1536, expected=1536)  # must not raise


def test_dimension_check_fails_with_both_values_in_message():
    with pytest.raises(ValueError) as exc_info:
        verify_dimension([0.1] * 384, expected=1536)
    message = str(exc_info.value)
    assert "384" in message
    assert "1536" in message


def test_dimension_check_fails_on_empty_vector():
    with pytest.raises(ValueError):
        verify_dimension([], expected=1536)
