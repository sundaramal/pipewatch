"""Tests for ExpiringCheck."""

from __future__ import annotations

import datetime

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.expiring import ExpiringCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="inner_pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="inner_fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _future(seconds: float = 3600) -> datetime.datetime:
    return _utc_now() + datetime.timedelta(seconds=seconds)


def _past(seconds: float = 3600) -> datetime.datetime:
    return _utc_now() - datetime.timedelta(seconds=seconds)


# ---------------------------------------------------------------------------
# Basic delegation
# ---------------------------------------------------------------------------

def test_expiring_passes_before_deadline_with_passing_inner():
    check = ExpiringCheck(wrapped=_PassCheck(), expires_at=_future())
    result = check.run()
    assert result.passed is True


def test_expiring_fails_before_deadline_with_failing_inner():
    check = ExpiringCheck(wrapped=_FailCheck(), expires_at=_future())
    result = check.run()
    assert result.passed is False
    assert result.message == "bad"


# ---------------------------------------------------------------------------
# Expiry behaviour
# ---------------------------------------------------------------------------

def test_expiring_fails_after_deadline_regardless_of_inner():
    check = ExpiringCheck(wrapped=_PassCheck(), expires_at=_past())
    result = check.run()
    assert result.passed is False
    assert "expired" in result.message.lower()


def test_expiring_message_contains_deadline_timestamp():
    deadline = _past()
    check = ExpiringCheck(wrapped=_PassCheck(), expires_at=deadline)
    result = check.run()
    assert deadline.isoformat() in result.message


def test_expiring_does_not_run_inner_after_deadline():
    """Inner check should be short-circuited once expired."""
    run_count = 0

    class _CountingCheck(BaseCheck):
        def __init__(self):
            super().__init__(name="counter")

        def run(self) -> CheckResult:
            nonlocal run_count
            run_count += 1
            return CheckResult(name=self.name, passed=True, message="ok")

    check = ExpiringCheck(wrapped=_CountingCheck(), expires_at=_past())
    check.run()
    assert run_count == 0


# ---------------------------------------------------------------------------
# Name handling
# ---------------------------------------------------------------------------

def test_expiring_uses_wrapped_name_by_default():
    inner = _PassCheck()
    check = ExpiringCheck(wrapped=inner, expires_at=_future())
    assert check.name == inner.name


def test_expiring_uses_custom_name_when_provided():
    check = ExpiringCheck(wrapped=_PassCheck(), expires_at=_future(), name="my_expiring")
    assert check.name == "my_expiring"


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_expiring_wrapped_property():
    inner = _PassCheck()
    check = ExpiringCheck(wrapped=inner, expires_at=_future())
    assert check.wrapped is inner


def test_expiring_expires_at_property():
    deadline = _future()
    check = ExpiringCheck(wrapped=_PassCheck(), expires_at=deadline)
    assert check.expires_at == deadline
