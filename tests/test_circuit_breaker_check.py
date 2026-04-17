"""Tests for CircuitBreakerCheck."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.circuit_breaker import CircuitBreakerCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="bad")


class _CountingFail(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="counting")
        self.calls = 0

    def run(self) -> CheckResult:
        self.calls += 1
        return CheckResult(passed=False, message="bad")


def test_passes_through_when_circuit_closed():
    cb = CircuitBreakerCheck(_PassCheck(), threshold=3)
    assert cb.run().passed is True


def test_fails_through_before_threshold():
    cb = CircuitBreakerCheck(_FailCheck(), threshold=3)
    for _ in range(2):
        result = cb.run()
        assert result.passed is False


def test_circuit_opens_after_threshold():
    inner = _CountingFail()
    cb = CircuitBreakerCheck(inner, threshold=3, reset_timeout=999)
    for _ in range(3):
        cb.run()
    # Circuit should now be open
    result = cb.run()
    assert result.passed is True
    assert "Circuit open" in result.message
    assert inner.calls == 3  # No more calls after circuit opens


def test_circuit_resets_after_timeout():
    inner = _CountingFail()
    cb = CircuitBreakerCheck(inner, threshold=2, reset_timeout=0.05)
    cb.run()
    cb.run()  # Opens circuit
    assert cb.run().passed is True  # Skipped

    time.sleep(0.1)
    # After timeout, circuit is half-open; probe runs
    result = cb.run()
    assert result.passed is False  # Real failure returned
    assert inner.calls == 3


def test_consecutive_failures_reset_on_pass():
    results = [False, False, True, False, False]
    idx = 0

    class _Toggle(BaseCheck):
        def __init__(self):
            super().__init__(name="toggle")

        def run(self):
            nonlocal idx
            r = results[idx]
            idx += 1
            return CheckResult(passed=r, message="")

    cb = CircuitBreakerCheck(_Toggle(), threshold=3, reset_timeout=999)
    cb.run()  # fail -> consecutive=1
    cb.run()  # fail -> consecutive=2
    cb.run()  # pass -> consecutive=0
    cb.run()  # fail -> consecutive=1
    result = cb.run()  # fail -> consecutive=2, NOT open
    assert result.passed is False


def test_name_defaults_to_wrapped_name():
    cb = CircuitBreakerCheck(_PassCheck(), threshold=2)
    assert "pass" in cb.name


def test_custom_name():
    cb = CircuitBreakerCheck(_PassCheck(), threshold=2, name="my_cb")
    assert cb.name == "my_cb"


def test_wrapped_property():
    inner = _PassCheck()
    cb = CircuitBreakerCheck(inner, threshold=2)
    assert cb.wrapped is inner
