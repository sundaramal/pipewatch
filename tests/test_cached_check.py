"""Tests for CachedCheck."""

import time

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.cached import CachedCheck


class _CountingCheck(BaseCheck):
    def __init__(self, name: str, passes: bool = True) -> None:
        super().__init__(name)
        self.call_count = 0
        self._passes = passes

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(
            name=self.name,
            passed=self._passes,
            message="ok" if self._passes else "fail",
        )


def test_cached_check_runs_wrapped_on_first_call():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=60)
    result = check.run()
    assert result.passed
    assert inner.call_count == 1


def test_cached_check_returns_cached_result_within_ttl():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=60)
    check.run()
    check.run()
    check.run()
    assert inner.call_count == 1


def test_cached_result_message_has_cached_prefix():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=60)
    check.run()
    result = check.run()
    assert result.message.startswith("[cached]")


def test_first_result_message_has_no_cached_prefix():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=60)
    result = check.run()
    assert not result.message.startswith("[cached]")


def test_cached_check_reruns_after_ttl_expires():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=0.05)
    check.run()
    time.sleep(0.1)
    check.run()
    assert inner.call_count == 2


def test_invalidate_forces_fresh_run():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=60)
    check.run()
    check.invalidate()
    check.run()
    assert inner.call_count == 2


def test_cached_check_propagates_failure():
    inner = _CountingCheck("inner", passes=False)
    check = CachedCheck("c", inner, ttl=60)
    result = check.run()
    assert not result.passed


def test_cached_failure_is_also_cached():
    inner = _CountingCheck("inner", passes=False)
    check = CachedCheck("c", inner, ttl=60)
    check.run()
    result = check.run()
    assert not result.passed
    assert inner.call_count == 1


def test_wrapped_property_returns_inner_check():
    inner = _CountingCheck("inner")
    check = CachedCheck("c", inner, ttl=30)
    assert check.wrapped is inner
