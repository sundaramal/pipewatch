"""Tests for the fallback_factory helper module."""

import pytest
from pipewatch.checks.fallback_factory import build_fallback_from_params
from pipewatch.checks.fallback import FallbackCheck
from pipewatch.checks.base import BaseCheck, CheckResult


class _OkCheck(BaseCheck):
    def __init__(self, **kwargs):
        super().__init__(name=kwargs.get("name", "ok"))

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _BadCheck(BaseCheck):
    def __init__(self, **kwargs):
        super().__init__(name=kwargs.get("name", "bad"))

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


_REGISTRY = {"ok": _OkCheck, "bad": _BadCheck}


def _build(type_name, params):
    cls = _REGISTRY[type_name]
    return cls(**params)


def test_builds_fallback_check_instance():
    fc = build_fallback_from_params(
        {"primary": {"type": "ok"}, "fallback": {"type": "bad"}}, _build
    )
    assert isinstance(fc, FallbackCheck)


def test_uses_custom_name():
    fc = build_fallback_from_params(
        {"primary": {"type": "ok"}, "fallback": {"type": "ok"}, "name": "myfb"}, _build
    )
    assert fc.name == "myfb"


def test_default_name_is_fallback():
    fc = build_fallback_from_params(
        {"primary": {"type": "ok"}, "fallback": {"type": "ok"}}, _build
    )
    assert fc.name == "fallback"


def test_raises_without_primary():
    with pytest.raises(ValueError, match="primary"):
        build_fallback_from_params({"fallback": {"type": "ok"}}, _build)


def test_raises_without_fallback():
    with pytest.raises(ValueError, match="fallback"):
        build_fallback_from_params({"primary": {"type": "ok"}}, _build)


def test_run_result_passes_when_primary_passes():
    fc = build_fallback_from_params(
        {"primary": {"type": "ok"}, "fallback": {"type": "bad"}}, _build
    )
    assert fc.run().passed
