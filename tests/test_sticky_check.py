"""Tests for StickyCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.sticky import StickyCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(passed=True, name=self.name, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(passed=False, name=self.name, message="bad")


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_sticky_passes_through_on_success():
    inner = _PassCheck()
    check = StickyCheck(inner)
    result = check.run()
    assert result.passed


def test_sticky_passes_through_multiple_successes():
    inner = _PassCheck()
    check = StickyCheck(inner)
    for _ in range(5):
        assert check.run().passed
    assert inner.call_count == 5


def test_sticky_fails_on_first_failure():
    inner = _FailCheck()
    check = StickyCheck(inner)
    result = check.run()
    assert not result.passed


def test_sticky_latches_after_first_failure():
    inner = _FailCheck()
    check = StickyCheck(inner)
    check.run()  # first failure — latches
    check.run()  # should NOT call inner again
    check.run()
    # Inner was only called once; subsequent calls used the cached result.
    assert inner.call_count == 1


def test_sticky_is_stuck_property():
    inner = _FailCheck()
    check = StickyCheck(inner)
    assert not check.is_stuck
    check.run()
    assert check.is_stuck


def test_sticky_reset_clears_latch():
    inner = _FailCheck()
    check = StickyCheck(inner)
    check.run()
    assert check.is_stuck
    check.reset()
    assert not check.is_stuck


def test_sticky_reset_allows_inner_to_run_again():
    inner = _FailCheck()
    check = StickyCheck(inner)
    check.run()          # latch
    check.reset()        # clear
    check.run()          # should call inner again
    assert inner.call_count == 2


def test_sticky_inherits_name_from_inner():
    inner = _PassCheck()
    check = StickyCheck(inner)
    assert check.name == inner.name


def test_sticky_accepts_custom_name():
    inner = _PassCheck()
    check = StickyCheck(inner, name="my-sticky")
    assert check.name == "my-sticky"


def test_sticky_wrapped_property():
    inner = _PassCheck()
    check = StickyCheck(inner)
    assert check.wrapped is inner


def test_sticky_latched_message_preserved():
    inner = _FailCheck()
    check = StickyCheck(inner)
    first = check.run()
    second = check.run()
    assert first.message == second.message
