"""Tests for ProfiledCheck and build_profiled_from_params."""
from __future__ import annotations

import time
from typing import Optional

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.profiled import ProfiledCheck
from pipewatch.checks.profiled_factory import build_profiled_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.registry import register_builtins


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


class _SlowCheck(BaseCheck):
    def __init__(self, delay: float = 0.05) -> None:
        super().__init__(name="slow")
        self._delay = delay

    def run(self) -> CheckResult:
        time.sleep(self._delay)
        return CheckResult(name=self.name, passed=True, message="done")


# ---------------------------------------------------------------------------
# ProfiledCheck unit tests
# ---------------------------------------------------------------------------

def test_profiled_passes_when_inner_passes():
    check = ProfiledCheck(wrapped=_PassCheck())
    result = check.run()
    assert result.passed is True


def test_profiled_fails_when_inner_fails():
    check = ProfiledCheck(wrapped=_FailCheck())
    result = check.run()
    assert result.passed is False


def test_profiled_preserves_inner_message():
    check = ProfiledCheck(wrapped=_FailCheck())
    result = check.run()
    assert result.message == "bad"


def test_profiled_default_name_includes_wrapped_name():
    check = ProfiledCheck(wrapped=_PassCheck(name="my_check"))
    assert "my_check" in check.name


def test_profiled_custom_name_is_used():
    check = ProfiledCheck(wrapped=_PassCheck(), name="custom_name")
    assert check.name == "custom_name"
    assert check.run().name == "custom_name"


def test_profiled_result_name_matches_check_name():
    check = ProfiledCheck(wrapped=_PassCheck(), name="prof")
    result = check.run()
    assert result.name == "prof"


def test_profiled_adds_wall_seconds_to_details():
    check = ProfiledCheck(wrapped=_SlowCheck(delay=0.05))
    result = check.run()
    assert "profile_wall_seconds" in result.details
    assert result.details["profile_wall_seconds"] >= 0.04


def test_profiled_adds_cpu_time_keys():
    check = ProfiledCheck(wrapped=_PassCheck())
    result = check.run()
    assert "profile_ru_utime" in result.details
    assert "profile_ru_stime" in result.details


def test_profiled_adds_maxrss_key():
    check = ProfiledCheck(wrapped=_PassCheck())
    result = check.run()
    assert "profile_ru_maxrss" in result.details
    assert isinstance(result.details["profile_ru_maxrss"], int)


def test_profiled_merges_existing_details():
    class _DetailCheck(BaseCheck):
        def __init__(self):
            super().__init__(name="detail")
        def run(self):
            return CheckResult(name=self.name, passed=True, message="", details={"foo": "bar"})

    check = ProfiledCheck(wrapped=_DetailCheck())
    result = check.run()
    assert result.details["foo"] == "bar"
    assert "profile_wall_seconds" in result.details


def test_wrapped_property_returns_inner_check():
    inner = _PassCheck()
    check = ProfiledCheck(wrapped=inner)
    assert check.wrapped is inner


# ---------------------------------------------------------------------------
# build_profiled_from_params tests
# ---------------------------------------------------------------------------

def _ensure_builtins():
    register_builtins()


def test_build_raises_without_check_key():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_profiled_from_params({})


def test_build_raises_for_non_dict_check():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_profiled_from_params({"check": "threshold"})


def test_build_returns_profiled_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "value": 5, "min": 0, "max": 10},
    }
    result = build_profiled_from_params(params)
    assert isinstance(result, ProfiledCheck)


def test_build_respects_custom_name():
    _ensure_builtins()
    params = {
        "name": "my_profiled",
        "check": {"type": "threshold", "value": 5, "min": 0, "max": 10},
    }
    check = build_profiled_from_params(params)
    assert check.name == "my_profiled"
