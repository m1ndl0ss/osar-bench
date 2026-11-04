"""Parsing and verdict helpers of the post-freeze modules."""
from osar.integrate import verdict


def test_verdicts():
    assert verdict(0.2, 0.1, 0.3, "higher") == "supported"
    assert verdict(0.2, -0.1, 0.3, "higher") == "not supported"
    assert verdict(-0.05, -0.09, -0.01, "lower") == "supported"
    assert verdict(0.0, -0.1, 0.1, "none") == "no difference"
    assert verdict(0.3, 0.1, 0.5, "none") == "difference"
