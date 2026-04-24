"""Tests for QuarantinedCheck."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.quarantined import QuarantinedCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, name=self.name, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, name=self.name, message="nope")


def test_passes_when_wrapped_passes():
    q = QuarantinedCheck(_PassCheck(), quarantine_seconds=30)
    result = q.run()
    assert result.passed


def test_fails_when_wrapped_fails_first_time():
    q = QuarantinedCheck(_FailCheck(), quarantine_seconds=30)
    result = q.run()
    assert not result.passed


def test_skips_after_failure_within_window():
    q = QuarantinedCheck(_FailCheck(), quarantine_seconds=30)
    q.run()  # triggers quarantine
    result = q.run()  # should be skipped
    assert result.passed
    assert "quarantined" in result.message


def test_not_quarantined_initially():
    q = QuarantinedCheck(_PassCheck(), quarantine_seconds=30)
    assert not q.is_quarantined


def test_is_quarantined_after_failure():
    q = QuarantinedCheck(_FailCheck(), quarantine_seconds=30)
    q.run()
    assert q.is_quarantined


def test_quarantine_expires_and_reruns():
    q = QuarantinedCheck(_FailCheck(), quarantine_seconds=1)
    q.run()  # fail + quarantine
    assert q.is_quarantined

    # fast-forward past the quarantine window
    with patch("pipewatch.checks.quarantined.time.monotonic", return_value=time.monotonic() + 2):
        assert not q.is_quarantined
        result = q.run()
    # inner check still fails, so result is failure again
    assert not result.passed


def test_name_is_auto_generated():
    q = QuarantinedCheck(_PassCheck(), quarantine_seconds=10)
    assert "pass" in q.name


def test_name_can_be_overridden():
    q = QuarantinedCheck(_PassCheck(), quarantine_seconds=10, name="my-check")
    assert q.name == "my-check"


def test_wrapped_property():
    inner = _PassCheck()
    q = QuarantinedCheck(inner, quarantine_seconds=10)
    assert q.wrapped is inner


def test_quarantine_seconds_property():
    q = QuarantinedCheck(_PassCheck(), quarantine_seconds=45)
    assert q.quarantine_seconds == 45


def test_invalid_quarantine_seconds_raises():
    with pytest.raises(ValueError):
        QuarantinedCheck(_PassCheck(), quarantine_seconds=0)

    with pytest.raises(ValueError):
        QuarantinedCheck(_PassCheck(), quarantine_seconds=-5)


def test_no_quarantine_on_passing_run():
    q = QuarantinedCheck(_PassCheck(), quarantine_seconds=30)
    q.run()
    assert not q.is_quarantined
