"""Tests for PinnedCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.pinned import PinnedCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


class _ToggleCheck(BaseCheck):
    """Alternates pass/fail on each call."""

    def __init__(self) -> None:
        super().__init__(name="toggle")
        self._call = 0

    def run(self) -> CheckResult:
        self._call += 1
        passed = self._call % 2 == 1  # odd calls pass, even calls fail
        return CheckResult(name=self.name, passed=passed, message=str(passed))


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_name_includes_inner_name() -> None:
    pc = PinnedCheck(_PassCheck())
    assert "pass" in pc.name


def test_custom_name_is_respected() -> None:
    pc = PinnedCheck(_PassCheck(), name="my-pin")
    assert pc.name == "my-pin"


def test_pinned_value_is_none_before_first_run() -> None:
    pc = PinnedCheck(_PassCheck())
    assert pc.pinned_value is None


def test_wrapped_property_returns_inner_check() -> None:
    inner = _PassCheck()
    pc = PinnedCheck(inner)
    assert pc.wrapped is inner


# ---------------------------------------------------------------------------
# First-run behaviour
# ---------------------------------------------------------------------------

def test_first_run_always_passes_for_passing_inner() -> None:
    pc = PinnedCheck(_PassCheck())
    result = pc.run()
    assert result.passed is True


def test_first_run_always_passes_for_failing_inner() -> None:
    pc = PinnedCheck(_FailCheck())
    result = pc.run()
    assert result.passed is True


def test_first_run_pins_pass_baseline() -> None:
    pc = PinnedCheck(_PassCheck())
    pc.run()
    assert pc.pinned_value is True


def test_first_run_pins_fail_baseline() -> None:
    pc = PinnedCheck(_FailCheck())
    pc.run()
    assert pc.pinned_value is False


# ---------------------------------------------------------------------------
# Subsequent runs — no drift
# ---------------------------------------------------------------------------

def test_second_run_passes_when_outcome_unchanged_pass() -> None:
    pc = PinnedCheck(_PassCheck())
    pc.run()          # pin
    result = pc.run() # same outcome
    assert result.passed is True


def test_second_run_passes_when_outcome_unchanged_fail() -> None:
    pc = PinnedCheck(_FailCheck())
    pc.run()
    result = pc.run()
    assert result.passed is True


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

def test_drift_detected_pass_to_fail() -> None:
    pc = PinnedCheck(_ToggleCheck())
    pc.run()          # call 1 → PASS, pinned as PASS
    result = pc.run() # call 2 → FAIL, drift!
    assert result.passed is False


def test_drift_message_contains_expected_and_actual() -> None:
    pc = PinnedCheck(_ToggleCheck())
    pc.run()
    result = pc.run()
    assert "PASS" in result.message
    assert "FAIL" in result.message


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

def test_reset_clears_pinned_value() -> None:
    pc = PinnedCheck(_PassCheck())
    pc.run()
    pc.reset()
    assert pc.pinned_value is None


def test_after_reset_first_run_repins() -> None:
    pc = PinnedCheck(_ToggleCheck())
    pc.run()   # pin as PASS
    pc.reset()
    result = pc.run()  # call 2 → FAIL, but reset so it re-pins
    assert result.passed is True
    assert pc.pinned_value is False
