"""Tests for build_retrying_fallback_from_params."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.retrying_fallback import RetryingFallbackCheck
from pipewatch.checks.retrying_fallback_factory import build_retrying_fallback_from_params
from pipewatch.checks.registry import register_builtins


def _ensure_builtins():
    try:
        register_builtins()
    except Exception:
        pass


class _SimplePass(BaseCheck):
    def __init__(self, **_):
        super().__init__(name="simple_pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


def _build_fn(cfg: dict) -> BaseCheck:
    """Minimal stand-in for build_check that always returns a passing check."""
    return _SimplePass()


# ---------------------------------------------------------------------------
# Happy-path
# ---------------------------------------------------------------------------

def test_build_returns_retrying_fallback_instance():
    params = {"check": {"type": "threshold"}, "fallback": {"type": "threshold"}}
    result = build_retrying_fallback_from_params(params, _build_fn)
    assert isinstance(result, RetryingFallbackCheck)


def test_build_respects_retries():
    params = {
        "check": {"type": "threshold"},
        "fallback": {"type": "threshold"},
        "retries": 5,
    }
    check = build_retrying_fallback_from_params(params, _build_fn)
    assert check.retries == 5


def test_build_default_retries_is_three():
    params = {"check": {"type": "threshold"}, "fallback": {"type": "threshold"}}
    check = build_retrying_fallback_from_params(params, _build_fn)
    assert check.retries == 3


def test_build_respects_custom_name():
    params = {
        "check": {"type": "threshold"},
        "fallback": {"type": "threshold"},
        "name": "my_rf_check",
    }
    check = build_retrying_fallback_from_params(params, _build_fn)
    assert check.name == "my_rf_check"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_build_raises_without_check_key():
    with pytest.raises(ValueError, match="'check'"):
        build_retrying_fallback_from_params({"fallback": {}}, _build_fn)


def test_build_raises_without_fallback_key():
    with pytest.raises(ValueError, match="'fallback'"):
        build_retrying_fallback_from_params({"check": {}}, _build_fn)


def test_build_raises_for_non_dict_check():
    with pytest.raises(TypeError, match="'check' must be a dict"):
        build_retrying_fallback_from_params(
            {"check": "not_a_dict", "fallback": {}}, _build_fn
        )


def test_build_raises_for_non_dict_fallback():
    with pytest.raises(TypeError, match="'fallback' must be a dict"):
        build_retrying_fallback_from_params(
            {"check": {}, "fallback": 42}, _build_fn
        )
