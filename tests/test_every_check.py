"""Tests for EveryCheck and its factory helper."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.every import EveryCheck
from pipewatch.checks.every_factory import build_every_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.registry import register_builtins


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, msg: str = "boom") -> None:
        super().__init__(name="fail")
        self._msg = msg

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message=self._msg)


# ---------------------------------------------------------------------------
# EveryCheck unit tests
# ---------------------------------------------------------------------------

def test_every_passes_with_no_sub_checks():
    result = EveryCheck().run()
    assert result.passed


def test_every_passes_when_all_sub_checks_pass():
    ev = EveryCheck()
    ev.add_check(_PassCheck()).add_check(_PassCheck())
    result = ev.run()
    assert result.passed
    assert "2" in result.message


def test_every_fails_on_first_failing_check():
    ev = EveryCheck()
    ev.add_check(_PassCheck())
    ev.add_check(_FailCheck(msg="something wrong"))
    ev.add_check(_PassCheck())
    result = ev.run()
    assert not result.passed
    assert "something wrong" in result.message


def test_every_short_circuits_after_first_failure():
    """Only the first failing check's message should appear."""
    ev = EveryCheck()
    ev.add_check(_FailCheck(msg="first fail"))
    ev.add_check(_FailCheck(msg="second fail"))
    result = ev.run()
    assert "first fail" in result.message
    assert "second fail" not in result.message


def test_every_checks_property_returns_copy():
    ev = EveryCheck()
    ev.add_check(_PassCheck())
    copy = ev.checks
    copy.clear()
    assert len(ev.checks) == 1


# ---------------------------------------------------------------------------
# Factory helper tests
# ---------------------------------------------------------------------------

def _ensure_builtins():
    register_builtins()


def test_build_every_returns_every_instance():
    _ensure_builtins()
    params = {"checks": [{"type": "threshold", "value": 5, "min": 0, "max": 10}]}
    result = build_every_from_params(params)
    assert isinstance(result, EveryCheck)


def test_build_every_raises_without_checks_key():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_every_from_params({})


def test_build_every_raises_with_empty_checks_list():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_every_from_params({"checks": []})


def test_build_every_raises_for_non_dict_entry():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_every_from_params({"checks": ["not-a-dict"]})


def test_build_every_respects_custom_name():
    _ensure_builtins()
    params = {
        "name": "my-every",
        "checks": [{"type": "threshold", "value": 1, "min": 0, "max": 5}],
    }
    ev = build_every_from_params(params)
    assert ev.name == "my-every"
