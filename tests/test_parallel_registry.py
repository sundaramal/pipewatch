"""Integration tests: ParallelCheck in the registry and factory."""
from __future__ import annotations

import pytest
from pipewatch.checks.registry import register_builtins, get, available
from pipewatch.checks.parallel import ParallelCheck
from pipewatch.checks.factory import build_check, CheckBuildError
from pipewatch.checks.base import BaseCheck, CheckResult


def _ensure_builtins():
    register_builtins()


class _P(BaseCheck):
    def __init__(self, name="p", **_):
        super().__init__(name)

    def run(self):
        return CheckResult(passed=True, message="ok")


def test_parallel_is_in_available():
    _ensure_builtins()
    assert "parallel" in available()


def test_registry_get_returns_parallel_class():
    _ensure_builtins()
    assert get("parallel") is ParallelCheck


def test_build_check_raises_for_parallel_without_checks_param():
    _ensure_builtins()
    with pytest.raises(CheckBuildError):
        build_check("p", "parallel", {})


def test_parallel_via_registry_all_pass():
    _ensure_builtins()
    params = {
        "checks": [
            {"type": "threshold", "name": "a", "params": {"value": 5, "min": 0, "max": 10}},
            {"type": "threshold", "name": "b", "params": {"value": 3, "min": 0, "max": 10}},
        ]
    }
    pc = build_check("my_p", "parallel", params)
    result = pc.run()
    assert result.passed


def test_parallel_via_registry_one_fail():
    _ensure_builtins()
    params = {
        "checks": [
            {"type": "threshold", "name": "ok", "params": {"value": 5, "min": 0, "max": 10}},
            {"type": "threshold", "name": "bad", "params": {"value": 50, "min": 0, "max": 10}},
        ]
    }
    pc = build_check("my_p", "parallel", params)
    result = pc.run()
    assert not result.passed
