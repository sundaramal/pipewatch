"""Tests for MemoizedCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.memoized import MemoizedCheck


class _CountingCheck(BaseCheck):
    def __init__(self, passes: bool = True) -> None:
        super().__init__(name="counter")
        self.call_count = 0
        self._passes = passes

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(
            name=self.name,
            passed=self._passes,
            message="ok" if self._passes else "fail",
        )


# ---------------------------------------------------------------------------
# Basic single-key memoization
# ---------------------------------------------------------------------------

def test_memoized_runs_wrapped_on_first_call():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner)
    result = check.run()
    assert result.passed is True
    assert inner.call_count == 1


def test_memoized_does_not_run_wrapped_on_second_call():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner)
    check.run()
    check.run()
    assert inner.call_count == 1


def test_memoized_result_on_second_call_has_memoized_prefix():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner)
    check.run()
    second = check.run()
    assert second.message.startswith("[memoized]")


def test_memoized_preserves_failure_result():
    inner = _CountingCheck(passes=False)
    check = MemoizedCheck(inner)
    check.run()
    second = check.run()
    assert second.passed is False


# ---------------------------------------------------------------------------
# Key-function behaviour
# ---------------------------------------------------------------------------

def test_different_keys_each_trigger_wrapped_run():
    inner = _CountingCheck(passes=True)
    counter = {"v": 0}

    def key_fn():
        return counter["v"]

    check = MemoizedCheck(inner, key_fn=key_fn)
    check.run()          # key=0
    counter["v"] = 1
    check.run()          # key=1
    assert inner.call_count == 2


def test_same_key_reuses_cache():
    inner = _CountingCheck(passes=True)
    key = {"v": "A"}
    check = MemoizedCheck(inner, key_fn=lambda: key["v"])
    check.run()   # key=A, runs
    check.run()   # key=A, cached
    key["v"] = "B"
    check.run()   # key=B, runs
    key["v"] = "A"
    check.run()   # key=A, cached again
    assert inner.call_count == 2


# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------

def test_invalidate_specific_key_forces_rerun():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner)   # default key=None
    check.run()
    check.invalidate(key=None)
    check.run()
    assert inner.call_count == 2


def test_invalidate_all_clears_cache():
    inner = _CountingCheck(passes=True)
    key = {"v": 0}
    check = MemoizedCheck(inner, key_fn=lambda: key["v"])
    check.run()          # key=0
    key["v"] = 1
    check.run()          # key=1
    check.invalidate(key=...)   # clear all
    key["v"] = 0
    check.run()          # key=0 again — should rerun
    assert inner.call_count == 3


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_default_name_falls_back_to_wrapped_name():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner)
    assert check.name == inner.name


def test_custom_name_overrides_wrapped_name():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner, name="my-memoized")
    assert check.name == "my-memoized"


def test_wrapped_property_returns_inner_check():
    inner = _CountingCheck(passes=True)
    check = MemoizedCheck(inner)
    assert check.wrapped is inner
