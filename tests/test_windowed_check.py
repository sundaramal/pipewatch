"""Tests for :class:`pipewatch.checks.windowed.WindowedCheck`."""
from __future__ import annotations

import time
from typing import Optional
from unittest.mock import patch

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.windowed import WindowedCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=True, name=self.name, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=False, name=self.name, message="boom")


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_windowed_passes_when_inner_passes():
    wc = WindowedCheck(_PassCheck(), window_seconds=60, threshold=2)
    result = wc.run()
    assert result.passed


def test_windowed_passes_below_threshold():
    """A single failure with threshold=2 should still report pass."""
    wc = WindowedCheck(_FailCheck(), window_seconds=60, threshold=2)
    result = wc.run()  # 1 failure < threshold 2
    assert result.passed


def test_windowed_fails_at_threshold():
    """Exactly `threshold` failures within the window → fail."""
    wc = WindowedCheck(_FailCheck(), window_seconds=60, threshold=3)
    for _ in range(2):
        r = wc.run()
        assert r.passed, "should still pass before threshold"
    result = wc.run()  # 3rd failure hits threshold
    assert not result.passed


def test_windowed_failure_message_contains_count():
    wc = WindowedCheck(_FailCheck(), window_seconds=60, threshold=2)
    wc.run()  # 1st
    result = wc.run()  # 2nd — triggers
    assert "2" in result.message
    assert "threshold=2" in result.message


def test_windowed_name_defaults_to_wrapped_name():
    inner = _PassCheck(name="my_check")
    wc = WindowedCheck(inner)
    assert "my_check" in wc.name


def test_windowed_custom_name():
    wc = WindowedCheck(_PassCheck(), name="custom")
    assert wc.name == "custom"


def test_windowed_exposes_wrapped():
    inner = _PassCheck()
    wc = WindowedCheck(inner)
    assert wc.wrapped is inner


def test_windowed_exposes_window_and_threshold():
    wc = WindowedCheck(_PassCheck(), window_seconds=30, threshold=5)
    assert wc.window_seconds == 30
    assert wc.threshold == 5


# ---------------------------------------------------------------------------
# Stale-entry eviction
# ---------------------------------------------------------------------------

def test_windowed_resets_after_window_expires():
    """Failures outside the window should not count toward the threshold."""
    wc = WindowedCheck(_FailCheck(), window_seconds=1.0, threshold=2)

    # Record one failure at t=0.
    with patch("pipewatch.checks.windowed.time.monotonic", return_value=0.0):
        wc.run()

    # Advance time beyond the window; the old failure is evicted.
    # A new failure at t=2.0 is the only one — below threshold.
    with patch("pipewatch.checks.windowed.time.monotonic", return_value=2.0):
        result = wc.run()

    assert result.passed, "stale failure should have been evicted"


def test_windowed_accumulates_within_window():
    """Multiple failures within the window accumulate correctly."""
    wc = WindowedCheck(_FailCheck(), window_seconds=10.0, threshold=3)

    for t in (0.0, 1.0):
        with patch("pipewatch.checks.windowed.time.monotonic", return_value=t):
            r = wc.run()
            assert r.passed

    with patch("pipewatch.checks.windowed.time.monotonic", return_value=2.0):
        result = wc.run()

    assert not result.passed
