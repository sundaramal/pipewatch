"""Tests for RetryingFallbackCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.retrying_fallback import RetryingFallbackCheck


class _PassCheck(BaseCheck):
    def __init__(self, name="pass"):
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name="fail"):
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="nope")


class _CountingCheck(BaseCheck):
    """Fails for the first *fail_times* calls, then passes."""

    def __init__(self, fail_times: int = 2, name="counting"):
        super().__init__(name=name)
        self._fail_times = fail_times
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        if self.call_count <= self._fail_times:
            return CheckResult(passed=False, message=f"fail #{self.call_count}")
        return CheckResult(passed=True, message="finally passed")


# ---------------------------------------------------------------------------
# Basic pass / fail behaviour
# ---------------------------------------------------------------------------

def test_passes_immediately_when_wrapped_passes():
    check = RetryingFallbackCheck(_PassCheck(), _FailCheck(), retries=3)
    result = check.run()
    assert result.passed


def test_falls_back_when_all_retries_exhausted():
    check = RetryingFallbackCheck(_FailCheck(), _PassCheck(), retries=2)
    result = check.run()
    # fallback passes
    assert result.passed
    assert "fallback" in result.message
    assert "2 attempt(s)" in result.message


def test_falls_back_and_fails_when_fallback_also_fails():
    check = RetryingFallbackCheck(_FailCheck(), _FailCheck(), retries=2)
    result = check.run()
    assert not result.passed


def test_retries_until_success():
    counting = _CountingCheck(fail_times=2)
    check = RetryingFallbackCheck(counting, _FailCheck(), retries=5)
    result = check.run()
    assert result.passed
    assert counting.call_count == 3  # failed twice, passed on 3rd


def test_wrapped_called_exactly_retries_times_on_all_fail():
    counting = _CountingCheck(fail_times=99)
    check = RetryingFallbackCheck(counting, _PassCheck(), retries=4)
    check.run()
    assert counting.call_count == 4


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_raises_if_retries_less_than_one():
    with pytest.raises(ValueError, match="retries must be >= 1"):
        RetryingFallbackCheck(_PassCheck(), _FailCheck(), retries=0)


def test_default_name_contains_wrapped_name():
    check = RetryingFallbackCheck(_PassCheck(name="my_check"), _FailCheck())
    assert "my_check" in check.name


def test_custom_name_is_used():
    check = RetryingFallbackCheck(_PassCheck(), _FailCheck(), name="custom")
    assert check.name == "custom"


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_wrapped_property():
    inner = _PassCheck()
    check = RetryingFallbackCheck(inner, _FailCheck())
    assert check.wrapped is inner


def test_fallback_property():
    fb = _PassCheck(name="fb")
    check = RetryingFallbackCheck(_FailCheck(), fb)
    assert check.fallback is fb


def test_retries_property():
    check = RetryingFallbackCheck(_PassCheck(), _FailCheck(), retries=7)
    assert check.retries == 7
