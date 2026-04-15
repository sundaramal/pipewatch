"""Tests for pipewatch.checks.timeout.TimeoutCheck."""

from __future__ import annotations

import time
from typing import Optional

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.timeout import TimeoutCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FastPass(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fast_pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FastFail(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fast_fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="nope")


class _SlowCheck(BaseCheck):
    def __init__(self, sleep: float = 5.0) -> None:
        super().__init__(name="slow_check")
        self._sleep = sleep

    def run(self) -> CheckResult:  # pragma: no cover
        time.sleep(self._sleep)
        return CheckResult(name=self.name, passed=True, message="done")


class _RaisingCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="raising_check")

    def run(self) -> CheckResult:
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_passes_when_wrapped_check_passes_quickly() -> None:
    tc = TimeoutCheck(check=_FastPass(), timeout_seconds=2.0)
    result = tc.run()
    assert result.passed is True
    assert result.name == "fast_pass"


def test_fails_when_wrapped_check_fails_quickly() -> None:
    tc = TimeoutCheck(check=_FastFail(), timeout_seconds=2.0)
    result = tc.run()
    assert result.passed is False
    assert "nope" in result.message


def test_fails_with_timeout_message_when_check_is_too_slow() -> None:
    tc = TimeoutCheck(check=_SlowCheck(sleep=5.0), timeout_seconds=0.1)
    result = tc.run()
    assert result.passed is False
    assert "timed out" in result.message
    assert "0.1" in result.message


def test_fails_when_wrapped_check_raises_exception() -> None:
    tc = TimeoutCheck(check=_RaisingCheck(), timeout_seconds=2.0)
    result = tc.run()
    assert result.passed is False
    assert "boom" in result.message


def test_custom_name_overrides_wrapped_name() -> None:
    tc = TimeoutCheck(check=_FastPass(), timeout_seconds=1.0, name="my_timeout")
    assert tc.name == "my_timeout"
    result = tc.run()
    assert result.name == "my_timeout"


def test_default_name_inherits_from_wrapped() -> None:
    inner = _FastPass()
    tc = TimeoutCheck(check=inner, timeout_seconds=1.0)
    assert tc.name == inner.name


def test_wrapped_property_returns_inner_check() -> None:
    inner = _FastPass()
    tc = TimeoutCheck(check=inner, timeout_seconds=1.0)
    assert tc.wrapped is inner


def test_invalid_timeout_raises_value_error() -> None:
    with pytest.raises(ValueError, match="positive"):
        TimeoutCheck(check=_FastPass(), timeout_seconds=0)


def test_negative_timeout_raises_value_error() -> None:
    with pytest.raises(ValueError, match="positive"):
        TimeoutCheck(check=_FastPass(), timeout_seconds=-1.0)


def test_timeout_check_registered_in_registry() -> None:
    from pipewatch.checks.registry import available, register_builtins
    register_builtins()
    assert "timeout" in available()
