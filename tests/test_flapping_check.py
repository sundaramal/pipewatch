"""Tests for pipewatch.checks.flapping.FlappingCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.flapping import FlappingCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


class _ToggleCheck(BaseCheck):
    """Alternates pass/fail on each call."""

    def __init__(self) -> None:
        super().__init__(name="toggle")
        self._state = True

    def run(self) -> CheckResult:
        result = CheckResult(passed=self._state, name=self.name, message="")
        self._state = not self._state
        return result


# ---------------------------------------------------------------------------
# Basic delegation
# ---------------------------------------------------------------------------

def test_delegates_pass_when_stable():
    check = FlappingCheck(_PassCheck(), threshold=3, window=5)
    for _ in range(5):
        r = check.run()
        assert r.passed


def test_delegates_fail_when_stable():
    check = FlappingCheck(_FailCheck(), threshold=3, window=5)
    # Stable failures — no flapping, so real result propagates
    for _ in range(5):
        r = check.run()
        assert not r.passed


# ---------------------------------------------------------------------------
# Flap detection
# ---------------------------------------------------------------------------

def test_flapping_suppresses_after_threshold():
    check = FlappingCheck(_ToggleCheck(), threshold=3, window=5)
    results = [check.run() for _ in range(6)]
    # After enough toggles the check should be suppressed (passed=True)
    suppressed = [r for r in results if "flapping" in (r.message or "")]
    assert len(suppressed) > 0


def test_flapping_result_is_passing():
    check = FlappingCheck(_ToggleCheck(), threshold=2, window=4)
    for _ in range(4):
        check.run()  # warm up history
    r = check.run()
    # Once flapping is detected the wrapper must return passed=True
    assert r.passed


def test_flapping_message_contains_state_change_count():
    check = FlappingCheck(_ToggleCheck(), threshold=2, window=4)
    for _ in range(3):
        check.run()
    r = check.run()
    if "flapping" in (r.message or ""):
        assert "state-changes" in r.message


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_wrapped_property():
    inner = _PassCheck()
    check = FlappingCheck(inner)
    assert check.wrapped is inner


def test_threshold_property():
    check = FlappingCheck(_PassCheck(), threshold=4)
    assert check.threshold == 4


def test_window_property():
    check = FlappingCheck(_PassCheck(), window=7)
    assert check.window == 7


def test_name_defaults_to_wrapped_name():
    inner = _PassCheck()
    check = FlappingCheck(inner)
    assert check.name == inner.name


def test_custom_name_overrides_wrapped_name():
    check = FlappingCheck(_PassCheck(), name="custom")
    assert check.name == "custom"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_single_run_never_flaps():
    check = FlappingCheck(_ToggleCheck(), threshold=1, window=5)
    r = check.run()
    # Only one entry in history — cannot have any transitions
    assert "flapping" not in (r.message or "")


def test_high_threshold_never_triggers():
    check = FlappingCheck(_ToggleCheck(), threshold=100, window=5)
    results = [check.run() for _ in range(10)]
    suppressed = [r for r in results if "flapping" in (r.message or "")]
    assert len(suppressed) == 0
