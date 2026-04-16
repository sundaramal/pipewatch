"""Tests for ScheduledCheck."""

from datetime import time
from unittest.mock import patch

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.scheduled import ScheduledCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="bad")


def _at(h: int, m: int):
    """Return a time object and patch target."""
    return time(h, m)


def _patch_now(h: int, m: int):
    from datetime import datetime
    return patch(
        "pipewatch.checks.scheduled.datetime",
        **{"now.return_value": datetime(2024, 1, 1, h, m, 30)},
    )


def test_runs_wrapped_check_inside_window():
    check = ScheduledCheck(_FailCheck(), start=time(8, 0), end=time(18, 0))
    with _patch_now(12, 0):
        result = check.run()
    assert not result.passed
    assert result.message == "bad"


def test_skips_outside_window():
    check = ScheduledCheck(_FailCheck(), start=time(8, 0), end=time(18, 0))
    with _patch_now(22, 0):
        result = check.run()
    assert result.passed
    assert "Skipped" in result.message


def test_passes_inside_window():
    check = ScheduledCheck(_PassCheck(), start=time(6, 0), end=time(20, 0))
    with _patch_now(10, 30):
        result = check.run()
    assert result.passed
    assert result.message == "ok"


def test_overnight_window_inside():
    check = ScheduledCheck(_PassCheck(), start=time(22, 0), end=time(6, 0))
    with _patch_now(23, 0):
        result = check.run()
    assert result.passed


def test_overnight_window_outside():
    check = ScheduledCheck(_FailCheck(), start=time(22, 0), end=time(6, 0))
    with _patch_now(12, 0):
        result = check.run()
    assert result.passed
    assert "Skipped" in result.message


def test_name_defaults_to_wrapped_name():
    check = ScheduledCheck(_PassCheck(), start=time(0, 0), end=time(23, 59))
    assert check.name == "pass"


def test_name_override():
    check = ScheduledCheck(_PassCheck(), start=time(0, 0), end=time(23, 59), name="custom")
    assert check.name == "custom"


def test_wrapped_property():
    inner = _PassCheck()
    check = ScheduledCheck(inner, start=time(0, 0), end=time(23, 59))
    assert check.wrapped is inner
