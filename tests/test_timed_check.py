"""Tests for TimedCheck."""
from __future__ import annotations

import time
from typing import Optional

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.timed import TimedCheck


class _PassCheck(BaseCheck):
    def __init__(self, sleep: float = 0.0) -> None:
        super().__init__(name="pass")
        self._sleep = sleep

    def run(self) -> CheckResult:
        time.sleep(self._sleep)
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, sleep: float = 0.0) -> None:
        super().__init__(name="fail")
        self._sleep = sleep

    def run(self) -> CheckResult:
        time.sleep(self._sleep)
        return CheckResult(passed=False, message="bad")


def test_timed_passes_when_wrapped_passes():
    check = TimedCheck(_PassCheck())
    result = check.run()
    assert result.passed


def test_timed_fails_when_wrapped_fails():
    check = TimedCheck(_FailCheck())
    result = check.run()
    assert not result.passed


def test_timed_message_contains_elapsed():
    check = TimedCheck(_PassCheck())
    result = check.run()
    assert "elapsed=" in result.message


def test_timed_no_limit_does_not_force_failure_on_slow_check():
    check = TimedCheck(_PassCheck(sleep=0.05))
    result = check.run()
    assert result.passed


def test_timed_exceeds_max_seconds_forces_failure():
    check = TimedCheck(_PassCheck(sleep=0.08), max_seconds=0.01)
    result = check.run()
    assert not result.passed
    assert "exceeds max=" in result.message


def test_timed_within_max_seconds_keeps_pass():
    check = TimedCheck(_PassCheck(sleep=0.0), max_seconds=5.0)
    result = check.run()
    assert result.passed


def test_timed_default_name_includes_wrapped_name():
    check = TimedCheck(_PassCheck())
    assert "pass" in check.name


def test_timed_custom_name():
    check = TimedCheck(_PassCheck(), name="my_timed")
    assert check.name == "my_timed"


def test_timed_wrapped_property():
    inner = _PassCheck()
    check = TimedCheck(inner)
    assert check.wrapped is inner
