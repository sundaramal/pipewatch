"""Tests for WeightedCheck."""
import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.weighted import WeightedCheck


class _PassCheck(BaseCheck):
    def __init__(self, name="pass"):
        super().__init__(name, {})
    def run(self):
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name="fail"):
        super().__init__(name, {})
    def run(self):
        return CheckResult(name=self.name, passed=False, message="bad")


def test_no_sub_checks_passes():
    wc = WeightedCheck("empty")
    result = wc.run()
    assert result.passed


def test_all_pass_equal_weights():
    wc = WeightedCheck("w", {"min_score": 1.0})
    wc.add_check(_PassCheck("a"), 1.0)
    wc.add_check(_PassCheck("b"), 1.0)
    assert wc.run().passed


def test_all_fail_returns_fail():
    wc = WeightedCheck("w", {"min_score": 0.5})
    wc.add_check(_FailCheck("a"), 1.0)
    wc.add_check(_FailCheck("b"), 1.0)
    assert not wc.run().passed


def test_partial_pass_meets_threshold():
    wc = WeightedCheck("w", {"min_score": 0.5})
    wc.add_check(_PassCheck("a"), 1.0)
    wc.add_check(_FailCheck("b"), 1.0)
    assert wc.run().passed


def test_partial_pass_below_threshold():
    wc = WeightedCheck("w", {"min_score": 0.8})
    wc.add_check(_PassCheck("a"), 1.0)
    wc.add_check(_FailCheck("b"), 4.0)
    result = wc.run()
    assert not result.passed


def test_unequal_weights_heavy_pass():
    wc = WeightedCheck("w", {"min_score": 0.8})
    wc.add_check(_PassCheck("heavy"), 9.0)
    wc.add_check(_FailCheck("light"), 1.0)
    assert wc.run().passed


def test_checks_property_returns_copy():
    wc = WeightedCheck("w")
    wc.add_check(_PassCheck(), 2.0)
    checks = wc.checks
    assert len(checks) == 1
    checks.clear()
    assert len(wc.checks) == 1  # original unaffected


def test_invalid_min_score_raises():
    with pytest.raises(ValueError):
        WeightedCheck("w", {"min_score": 1.5})


def test_invalid_min_score_negative_raises():
    """min_score below 0.0 should also be rejected."""
    with pytest.raises(ValueError):
        WeightedCheck("w", {"min_score": -0.1})


def test_invalid_weight_raises():
    wc = WeightedCheck("w")
    with pytest.raises(ValueError):
        wc.add_check(_PassCheck(), 0.0)


def test_negative_weight_raises():
    """Negative weights should be rejected just like zero weights."""
    wc = WeightedCheck("w")
    with pytest.raises(ValueError):
        wc.add_check(_PassCheck(), -1.0)


def test_message_contains_sub_check_names():
    wc = WeightedCheck("w", {"min_score": 0.5})
    wc.add_check(_PassCheck("alpha"), 1.0)
    wc.add_check(_FailCheck("beta"), 1.0)
    result = wc.run()
    assert "alpha" in result.message
    assert "beta" in result.message
