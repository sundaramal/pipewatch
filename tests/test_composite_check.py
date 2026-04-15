"""Tests for pipewatch.checks.composite.CompositeCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.composite import CompositeCheck


# ---------------------------------------------------------------------------
# Minimal stub checks
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, detail="ok")


class _FailCheck(BaseCheck):
    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, detail="bad")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_composite_passes_when_all_sub_checks_pass():
    check = CompositeCheck("all_good", [_PassCheck("p1"), _PassCheck("p2")])
    result = check.run()
    assert result.passed is True


def test_composite_fails_when_any_sub_check_fails():
    check = CompositeCheck("mixed", [_PassCheck("p1"), _FailCheck("f1")])
    result = check.run()
    assert result.passed is False


def test_composite_fails_when_all_sub_checks_fail():
    check = CompositeCheck("all_bad", [_FailCheck("f1"), _FailCheck("f2")])
    result = check.run()
    assert result.passed is False


def test_composite_detail_mentions_failure_count():
    check = CompositeCheck("mixed", [_PassCheck("p1"), _FailCheck("f1"), _FailCheck("f2")])
    result = check.run()
    assert "2 of 3" in result.detail


def test_composite_detail_all_pass_message():
    check = CompositeCheck("all_good", [_PassCheck("p1")])
    result = check.run()
    assert "All sub-checks passed" in result.detail


def test_composite_name_is_preserved():
    check = CompositeCheck("my_composite", [_PassCheck("p1")])
    result = check.run()
    assert result.name == "my_composite"


def test_composite_checks_property_returns_copy():
    inner = [_PassCheck("p1"), _FailCheck("f1")]
    check = CompositeCheck("c", inner)
    returned = check.checks
    assert returned == inner
    # Mutating the returned list must not affect the internal list
    returned.clear()
    assert len(check.checks) == 2


def test_composite_raises_on_empty_checks():
    with pytest.raises(ValueError, match="at least one"):
        CompositeCheck("empty", [])


def test_composite_single_pass_check():
    check = CompositeCheck("solo", [_PassCheck("only")])
    result = check.run()
    assert result.passed is True


def test_composite_single_fail_check():
    check = CompositeCheck("solo", [_FailCheck("only")])
    result = check.run()
    assert result.passed is False
