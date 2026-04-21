"""Tests for ClampedCheck and its factory helper."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.clamped import ClampedCheck
from pipewatch.checks.clamped_factory import build_clamped_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.registry import register_builtins


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _ValueCheck(BaseCheck):
    """Returns a fixed numeric string as its message."""

    def __init__(self, value: float, passed: bool = True, name: str = "value") -> None:
        super().__init__(name=name)
        self._value = value
        self._passed = passed

    def run(self) -> CheckResult:
        return CheckResult(passed=self._passed, message=str(self._value))


class _TextCheck(BaseCheck):
    """Returns a non-numeric message."""

    def __init__(self) -> None:
        super().__init__(name="text")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


# ---------------------------------------------------------------------------
# ClampedCheck unit tests
# ---------------------------------------------------------------------------

def test_clamped_passes_through_value_within_range():
    check = ClampedCheck(_ValueCheck(50.0), min_val=0.0, max_val=100.0)
    result = check.run()
    assert result.passed is True
    assert float(result.message) == 50.0


def test_clamped_raises_value_to_min():
    check = ClampedCheck(_ValueCheck(-10.0), min_val=0.0)
    result = check.run()
    assert float(result.message) == 0.0


def test_clamped_lowers_value_to_max():
    check = ClampedCheck(_ValueCheck(200.0), max_val=100.0)
    result = check.run()
    assert float(result.message) == 100.0


def test_clamped_preserves_passed_flag_from_inner():
    check = ClampedCheck(_ValueCheck(5.0, passed=False), min_val=0.0, max_val=10.0)
    result = check.run()
    assert result.passed is False
    assert float(result.message) == 5.0


def test_clamped_non_numeric_message_passes_through():
    check = ClampedCheck(_TextCheck(), min_val=0.0, max_val=100.0)
    result = check.run()
    assert result.message == "ok"


def test_clamped_default_name_includes_wrapped_name():
    inner = _ValueCheck(1.0, name="my_check")
    check = ClampedCheck(inner)
    assert "my_check" in check.name


def test_clamped_custom_name_is_used():
    check = ClampedCheck(_ValueCheck(1.0), name="custom")
    assert check.name == "custom"


def test_clamped_raises_when_min_greater_than_max():
    with pytest.raises(ValueError):
        ClampedCheck(_ValueCheck(1.0), min_val=10.0, max_val=5.0)


def test_clamped_no_bounds_does_not_alter_value():
    check = ClampedCheck(_ValueCheck(999.0))
    result = check.run()
    assert float(result.message) == 999.0


# ---------------------------------------------------------------------------
# Factory helper tests
# ---------------------------------------------------------------------------

def _ensure_builtins():
    register_builtins()


def test_build_clamped_raises_without_check_key():
    _ensure_builtins()
    with pytest.raises(CheckBuildError, match="check"):
        build_clamped_from_params({"min_val": 0})


def test_build_clamped_raises_for_non_dict_check():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_clamped_from_params({"check": "threshold"})


def test_build_clamped_raises_without_type_in_inner_cfg():
    _ensure_builtins()
    with pytest.raises(CheckBuildError, match="type"):
        build_clamped_from_params({"check": {"params": {}}})


def test_build_clamped_returns_clamped_instance():
    _ensure_builtins()
    instance = build_clamped_from_params({
        "check": {"type": "threshold", "params": {"value": 50, "min": 0, "max": 100}},
        "min_val": 0,
        "max_val": 100,
    })
    assert isinstance(instance, ClampedCheck)


def test_build_clamped_raises_for_invalid_bounds():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_clamped_from_params({
            "check": {"type": "threshold", "params": {"value": 50, "min": 0, "max": 100}},
            "min_val": 100,
            "max_val": 0,
        })
