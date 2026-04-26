"""Tests for SuppressedCheck."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.suppressed import SuppressedCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, name=self.name, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, name=self.name, message="broken")


_START = datetime.time(2, 0)   # 02:00 UTC
_END   = datetime.time(4, 0)   # 04:00 UTC
_INSIDE  = datetime.datetime(2024, 1, 1, 3, 0)   # 03:00 — inside window
_OUTSIDE = datetime.datetime(2024, 1, 1, 5, 0)   # 05:00 — outside window


def _make(wrapped: BaseCheck, **kw) -> SuppressedCheck:
    return SuppressedCheck(wrapped, start=_START, end=_END, **kw)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_name_includes_wrapped_name():
    sc = _make(_FailCheck())
    assert "fail" in sc.name


def test_custom_name_is_used():
    sc = _make(_FailCheck(), name="my-suppressed")
    assert sc.name == "my-suppressed"


def test_wrapped_property_returns_inner_check():
    inner = _FailCheck()
    sc = _make(inner)
    assert sc.wrapped is inner


def test_raises_for_non_base_check():
    with pytest.raises(TypeError):
        SuppressedCheck("not-a-check", start=_START, end=_END)  # type: ignore


def test_raises_for_bad_time_types():
    with pytest.raises(TypeError):
        SuppressedCheck(_FailCheck(), start="02:00", end="04:00")  # type: ignore


# ---------------------------------------------------------------------------
# Window logic
# ---------------------------------------------------------------------------

def test_in_window_true_when_inside():
    sc = _make(_FailCheck())
    assert sc._in_window(_INSIDE) is True


def test_in_window_false_when_outside():
    sc = _make(_FailCheck())
    assert sc._in_window(_OUTSIDE) is False


def test_overnight_window():
    """Window spanning midnight, e.g. 22:00–02:00."""
    sc = SuppressedCheck(
        _FailCheck(),
        start=datetime.time(22, 0),
        end=datetime.time(2, 0),
    )
    assert sc._in_window(datetime.datetime(2024, 1, 1, 23, 0)) is True
    assert sc._in_window(datetime.datetime(2024, 1, 1, 1, 0)) is True
    assert sc._in_window(datetime.datetime(2024, 1, 1, 3, 0)) is False


# ---------------------------------------------------------------------------
# run() behaviour
# ---------------------------------------------------------------------------

def test_failure_suppressed_inside_window():
    sc = _make(_FailCheck())
    with patch("pipewatch.checks.suppressed.datetime.datetime") as mock_dt:
        mock_dt.utcnow.return_value = _INSIDE
        result = sc.run()
    assert result.passed is True
    assert "suppressed" in result.message


def test_failure_not_suppressed_outside_window():
    sc = _make(_FailCheck())
    with patch("pipewatch.checks.suppressed.datetime.datetime") as mock_dt:
        mock_dt.utcnow.return_value = _OUTSIDE
        result = sc.run()
    assert result.passed is False


def test_pass_unchanged_inside_window():
    sc = _make(_PassCheck())
    with patch("pipewatch.checks.suppressed.datetime.datetime") as mock_dt:
        mock_dt.utcnow.return_value = _INSIDE
        result = sc.run()
    assert result.passed is True
    assert "suppressed" not in result.message


def test_pass_unchanged_outside_window():
    sc = _make(_PassCheck())
    with patch("pipewatch.checks.suppressed.datetime.datetime") as mock_dt:
        mock_dt.utcnow.return_value = _OUTSIDE
        result = sc.run()
    assert result.passed is True
