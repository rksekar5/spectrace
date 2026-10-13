import pytest


@pytest.mark.requirements("REQ-A", "REQ-B")
def test_a():
    """Illustrative source declaration, not proof of behavior."""


@pytest.mark.requirements("REQ-A", "REQ-TYPO", "REQ-TYPO")
def test_b():
    """The repeated unknown reference is reported once."""
