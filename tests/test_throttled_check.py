"""Tests for ThrottledCheck."""
from __future__ import annotations

import time

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.throttled import ThrottledCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="pass")
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(passed=True, name=self.name, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="fail")
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(passed=False, name=self.name, message="bad")


def test_first_call_executes_wrapped():
    inner = _PassCheck()
    check = ThrottledCheck(inner, max_calls=1, window_seconds=60)
    result = check.run()
    assert result.passed
    assert inner.call_count == 1


def test_second_call_within_window_is_skipped():
    inner = _PassCheck()
    check = ThrottledCheck(inner, max_calls=1, window_seconds=60)
    check.run()
    result = check.run()
    assert result.passed
    assert "throttled" in result.message
    assert inner.call_count == 1


def test_multiple_calls_allowed_within_limit():
    inner = _PassCheck()
    check = ThrottledCheck(inner, max_calls=3, window_seconds=60)
    for _ in range(3):
        r = check.run()
        assert "throttled" not in r.message
    assert inner.call_count == 3
    # 4th call should be throttled
    r = check.run()
    assert "throttled" in r.message
    assert inner.call_count == 3


def test_throttled_result_passes_even_when_wrapped_would_fail():
    inner = _FailCheck()
    check = ThrottledCheck(inner, max_calls=1, window_seconds=60)
    check.run()  # consume the one allowed call
    result = check.run()
    assert result.passed  # skipped → pass
    assert inner.call_count == 1


def test_calls_allowed_again_after_window_expires():
    inner = _PassCheck()
    check = ThrottledCheck(inner, max_calls=1, window_seconds=0.05)
    check.run()
    time.sleep(0.1)
    result = check.run()
    assert "throttled" not in result.message
    assert inner.call_count == 2


def test_default_name_includes_wrapped_name():
    inner = _PassCheck()
    check = ThrottledCheck(inner)
    assert "pass" in check.name


def test_custom_name_is_used():
    inner = _PassCheck()
    check = ThrottledCheck(inner, name="my_throttled")
    assert check.name == "my_throttled"


def test_wrapped_property():
    inner = _PassCheck()
    check = ThrottledCheck(inner)
    assert check.wrapped is inner
