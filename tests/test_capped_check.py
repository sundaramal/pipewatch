"""Tests for CappedCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.capped import CappedCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, name=self.name, details="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, name=self.name, details="bad")


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_cap_is_three():
    check = CappedCheck(_PassCheck())
    assert check.cap == 3


def test_custom_cap_is_stored():
    check = CappedCheck(_PassCheck(), cap=5)
    assert check.cap == 5


def test_invalid_cap_raises():
    with pytest.raises(ValueError):
        CappedCheck(_PassCheck(), cap=0)


def test_name_defaults_to_wrapped_name():
    inner = _PassCheck()
    check = CappedCheck(inner)
    assert check.name == inner.name


def test_custom_name_overrides():
    check = CappedCheck(_PassCheck(), name="my-cap")
    assert check.name == "my-cap"


# ---------------------------------------------------------------------------
# Passing behaviour
# ---------------------------------------------------------------------------

def test_pass_result_is_forwarded():
    check = CappedCheck(_PassCheck())
    result = check.run()
    assert result.passed is True


def test_pass_resets_consecutive_failures():
    inner = _FailCheck()
    check = CappedCheck(inner, cap=2)
    check.run()  # fail 1
    check.run()  # fail 2
    assert check.consecutive_failures == 2

    # swap to a passing inner by resetting via a fresh wrapper
    pass_check = CappedCheck(_PassCheck(), cap=2)
    pass_check.run()
    assert pass_check.consecutive_failures == 0


# ---------------------------------------------------------------------------
# Failure counting
# ---------------------------------------------------------------------------

def test_failures_below_cap_are_forwarded_unchanged():
    check = CappedCheck(_FailCheck(), cap=3)
    for _ in range(3):
        result = check.run()
        assert result.passed is False
        assert "cap=" not in (result.details or "")


def test_failure_beyond_cap_includes_cap_notice():
    check = CappedCheck(_FailCheck(), cap=2)
    check.run()  # 1
    check.run()  # 2 — at cap
    result = check.run()  # 3 — beyond cap
    assert result.passed is False
    assert "cap=2 hit" in (result.details or "")


def test_consecutive_failures_increments_correctly():
    check = CappedCheck(_FailCheck(), cap=10)
    for i in range(1, 6):
        check.run()
        assert check.consecutive_failures == i


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_counter():
    check = CappedCheck(_FailCheck(), cap=2)
    check.run()
    check.run()
    assert check.consecutive_failures == 2
    check.reset()
    assert check.consecutive_failures == 0


def test_after_reset_cap_applies_fresh():
    check = CappedCheck(_FailCheck(), cap=1)
    check.run()  # 1 — at cap
    check.run()  # 2 — beyond cap, notice present
    check.reset()
    result = check.run()  # 1 again — should NOT have cap notice
    assert "cap=" not in (result.details or "")
