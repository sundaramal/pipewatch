"""Tests for HedgedCheck and build_hedged_from_params."""
from __future__ import annotations

import time
import threading
from typing import Optional

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.hedged import HedgedCheck
from pipewatch.checks.hedged_factory import build_hedged_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.registry import register_builtins


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self, delay: float = 0.0, name: str = "pass") -> None:
        super().__init__(name=name)
        self._delay = delay

    def run(self) -> CheckResult:
        if self._delay:
            time.sleep(self._delay)
        return CheckResult(passed=True, message="ok", name=self.name)


class _FailCheck(BaseCheck):
    def __init__(self, delay: float = 0.0, name: str = "fail") -> None:
        super().__init__(name=name)
        self._delay = delay

    def run(self) -> CheckResult:
        if self._delay:
            time.sleep(self._delay)
        return CheckResult(passed=False, message="fail", name=self.name)


# ---------------------------------------------------------------------------
# HedgedCheck unit tests
# ---------------------------------------------------------------------------

def test_hedged_returns_pass_when_primary_fast():
    check = HedgedCheck(_PassCheck(), _FailCheck(), hedge_after=5.0)
    result = check.run()
    assert result.passed


def test_hedged_returns_fail_when_primary_fast_and_fails():
    check = HedgedCheck(_FailCheck(), _PassCheck(), hedge_after=5.0)
    result = check.run()
    assert not result.passed


def test_hedged_uses_secondary_when_primary_is_slow():
    # Primary takes 0.3 s, hedge fires after 0.05 s → secondary wins.
    primary = _FailCheck(delay=0.3, name="slow-primary")
    secondary = _PassCheck(delay=0.0, name="fast-secondary")
    check = HedgedCheck(primary, secondary, hedge_after=0.05)
    result = check.run()
    assert result.passed


def test_hedged_name_defaults_to_wrapped_name():
    check = HedgedCheck(_PassCheck(name="my-check"), _FailCheck())
    assert "my-check" in check.name


def test_hedged_custom_name():
    check = HedgedCheck(_PassCheck(), _FailCheck(), name="custom")
    assert check.name == "custom"


def test_hedged_wrapped_property():
    primary = _PassCheck()
    check = HedgedCheck(primary, _FailCheck())
    assert check.wrapped is primary


def test_hedged_secondary_property():
    secondary = _FailCheck()
    check = HedgedCheck(_PassCheck(), secondary)
    assert check.secondary is secondary


def test_hedged_hedge_after_property():
    check = HedgedCheck(_PassCheck(), _FailCheck(), hedge_after=2.5)
    assert check.hedge_after == 2.5


# ---------------------------------------------------------------------------
# build_hedged_from_params tests
# ---------------------------------------------------------------------------

def _ensure_builtins():
    try:
        register_builtins()
    except Exception:
        pass


def test_build_raises_without_primary():
    _ensure_builtins()
    with pytest.raises(CheckBuildError, match="primary"):
        build_hedged_from_params({"secondary": {"type": "threshold", "value": 5}})


def test_build_raises_without_secondary():
    _ensure_builtins()
    with pytest.raises(CheckBuildError, match="secondary"):
        build_hedged_from_params({"primary": {"type": "threshold", "value": 5}})


def test_build_raises_for_non_dict_primary():
    _ensure_builtins()
    with pytest.raises(CheckBuildError, match="primary"):
        build_hedged_from_params({"primary": "bad", "secondary": {"type": "threshold", "value": 5}})


def test_build_returns_hedged_instance():
    _ensure_builtins()
    params = {
        "primary": {"type": "threshold", "value": 5, "min": 1, "max": 10},
        "secondary": {"type": "threshold", "value": 5, "min": 1, "max": 10},
        "hedge_after": 0.5,
    }
    instance = build_hedged_from_params(params)
    assert isinstance(instance, HedgedCheck)
    assert instance.hedge_after == 0.5


def test_build_default_hedge_after():
    _ensure_builtins()
    params = {
        "primary": {"type": "threshold", "value": 5, "min": 1, "max": 10},
        "secondary": {"type": "threshold", "value": 5, "min": 1, "max": 10},
    }
    instance = build_hedged_from_params(params)
    assert instance.hedge_after == 1.0
