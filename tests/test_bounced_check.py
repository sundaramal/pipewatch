"""Tests for BouncedCheck and build_bounced_from_params."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.bounced import BouncedCheck
from pipewatch.checks.bounced_factory import build_bounced_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.registry import register_builtins


class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name=name)
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name=name)
        self.call_count = 0

    def run(self) -> CheckResult:
        self.call_count += 1
        return CheckResult(name=self.name, passed=False, message="nope")


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_first_run_delegates_to_wrapped():
    inner = _PassCheck()
    bc = BouncedCheck(check=inner, gap_seconds=60)
    result = bc.run()
    assert result.passed is True
    assert inner.call_count == 1


def test_second_run_within_gap_returns_bounced_result():
    inner = _PassCheck()
    bc = BouncedCheck(check=inner, gap_seconds=60)
    bc.run()  # first — sets last_run
    result = bc.run()  # second — within gap
    assert result.passed is True
    assert inner.call_count == 1  # inner NOT called again
    assert "bounced" in result.message


def test_second_run_after_gap_delegates_again():
    inner = _PassCheck()
    bc = BouncedCheck(check=inner, gap_seconds=0.05)
    bc.run()
    time.sleep(0.1)
    bc.run()
    assert inner.call_count == 2


def test_bounced_result_preserves_pass_flag_from_last():
    inner = _FailCheck()
    bc = BouncedCheck(check=inner, gap_seconds=60)
    bc.run()
    result = bc.run()
    assert result.passed is False
    assert "bounced" in result.message


def test_name_defaults_to_wrapped_name():
    inner = _PassCheck(name="my-check")
    bc = BouncedCheck(check=inner, gap_seconds=1)
    assert bc.name == "my-check"


def test_custom_name_overrides_wrapped_name():
    inner = _PassCheck(name="inner")
    bc = BouncedCheck(check=inner, gap_seconds=1, name="outer")
    assert bc.name == "outer"


def test_negative_gap_raises():
    with pytest.raises(ValueError, match="gap_seconds"):
        BouncedCheck(check=_PassCheck(), gap_seconds=-1)


def test_wrapped_property():
    inner = _PassCheck()
    bc = BouncedCheck(check=inner, gap_seconds=5)
    assert bc.wrapped is inner


def test_gap_seconds_property():
    inner = _PassCheck()
    bc = BouncedCheck(check=inner, gap_seconds=3.5)
    assert bc.gap_seconds == 3.5


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _ensure_builtins():
    register_builtins()


def test_factory_raises_without_check_key():
    _ensure_builtins()
    with pytest.raises(CheckBuildError, match="'check'"):
        build_bounced_from_params({"gap_seconds": 5})


def test_factory_raises_for_invalid_check_cfg():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_bounced_from_params({"check": "not-a-dict"})


def test_factory_builds_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "gap_seconds": 30,
        "name": "my-bounced",
    }
    bc = build_bounced_from_params(params)
    assert isinstance(bc, BouncedCheck)
    assert bc.name == "my-bounced"
    assert bc.gap_seconds == 30.0


def test_factory_defaults_gap_to_one():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
    }
    bc = build_bounced_from_params(params)
    assert bc.gap_seconds == 1.0
