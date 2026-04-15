"""Tests for pipewatch.checks.retry.RetryCheck."""

from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.retry import RetryCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _AlwaysPass(BaseCheck):
    def __init__(self):
        super().__init__(name="always_pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _AlwaysFail(BaseCheck):
    def __init__(self):
        super().__init__(name="always_fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


class _FailThenPass(BaseCheck):
    """Fails for the first *fail_times* calls, then passes."""

    def __init__(self, fail_times: int = 1):
        super().__init__(name="fail_then_pass")
        self._remaining_failures = fail_times
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            return CheckResult(name=self.name, passed=False, message="transient")
        return CheckResult(name=self.name, passed=True, message="recovered")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_retry_passes_immediately_when_wrapped_passes():
    inner = _AlwaysPass()
    check = RetryCheck(inner, max_attempts=3)
    result = check.run()
    assert result.passed


def test_retry_fails_after_all_attempts_exhausted():
    inner = _AlwaysFail()
    check = RetryCheck(inner, max_attempts=3)
    result = check.run()
    assert not result.passed
    assert "3 attempt(s)" in result.message


def test_retry_recovers_on_second_attempt():
    inner = _FailThenPass(fail_times=1)
    check = RetryCheck(inner, max_attempts=3)
    result = check.run()
    assert result.passed
    assert inner.call_count == 2


def test_retry_recovers_on_third_attempt():
    inner = _FailThenPass(fail_times=2)
    check = RetryCheck(inner, max_attempts=3)
    result = check.run()
    assert result.passed
    assert inner.call_count == 3


def test_retry_name_includes_wrapped_check_name():
    inner = _AlwaysPass()
    check = RetryCheck(inner, max_attempts=2)
    assert "always_pass" in check.name


def test_retry_wrapped_property_returns_inner_check():
    inner = _AlwaysPass()
    check = RetryCheck(inner)
    assert check.wrapped is inner


def test_retry_max_attempts_one_does_not_retry():
    inner = _FailThenPass(fail_times=1)
    check = RetryCheck(inner, max_attempts=1)
    result = check.run()
    assert not result.passed
    assert inner.call_count == 1


def test_retry_raises_for_invalid_max_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        RetryCheck(_AlwaysPass(), max_attempts=0)


def test_retry_result_name_reflects_wrapper():
    inner = _AlwaysFail()
    check = RetryCheck(inner, max_attempts=2)
    result = check.run()
    assert result.name == check.name
