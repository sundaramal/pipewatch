"""Tests for RateLimitedCheck."""

from __future__ import annotations

import time
from typing import Optional

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.ratelimited import RateLimitedCheck


class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name=name)
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name=name)
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(name=self.name, passed=False, message="fail")


def test_first_run_executes_wrapped():
    inner = _PassCheck()
    check = RateLimitedCheck(inner, min_interval=60)
    result = check.run()
    assert result.passed
    assert inner.call_count == 1


def test_second_run_within_interval_is_skipped():
    inner = _PassCheck()
    check = RateLimitedCheck(inner, min_interval=60)
    check.run()
    result = check.run()
    assert result.passed
    assert "Skipped" in result.message
    assert inner.call_count == 1


def test_run_after_interval_executes_wrapped(monkeypatch):
    inner = _PassCheck()
    check = RateLimitedCheck(inner, min_interval=1)
    check.run()
    # Advance monotonic clock by patching _last_run
    check._last_run -= 2
    result = check.run()
    assert result.passed
    assert inner.call_count == 2


def test_skipped_result_is_pass_even_if_wrapped_would_fail():
    inner = _FailCheck()
    check = RateLimitedCheck(inner, min_interval=60)
    check.run()  # first run executes and fails
    result = check.run()  # second run is skipped → pass
    assert result.passed
    assert inner.call_count == 1


def test_name_defaults_to_wrapped_name():
    inner = _PassCheck(name="my-check")
    check = RateLimitedCheck(inner, min_interval=10)
    assert check.name == "my-check"


def test_name_can_be_overridden():
    inner = _PassCheck(name="my-check")
    check = RateLimitedCheck(inner, min_interval=10, name="custom")
    assert check.name == "custom"


def test_wrapped_property():
    inner = _PassCheck()
    check = RateLimitedCheck(inner, min_interval=5)
    assert check.wrapped is inner


def test_zero_interval_always_executes():
    inner = _PassCheck()
    check = RateLimitedCheck(inner, min_interval=0)
    check.run()
    check.run()
    assert inner.call_count == 2
