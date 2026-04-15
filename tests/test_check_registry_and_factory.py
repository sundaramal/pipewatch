"""Tests for the check registry and factory modules."""

import pytest
from pipewatch.checks.registry import register, get, available, _REGISTRY
from pipewatch.checks.factory import build_check, build_checks, CheckBuildError
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.builtin import ThresholdCheck, FreshnessCheck
from pipewatch.config import CheckConfig


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_builtins_are_registered():
    names = available()
    assert "threshold" in names
    assert "freshness" in names


def test_get_returns_correct_class():
    assert get("threshold") is ThresholdCheck
    assert get("freshness") is FreshnessCheck


def test_get_raises_key_error_for_unknown():
    with pytest.raises(KeyError, match="unknown_type"):
        get("unknown_type")


def test_register_custom_check():
    class _DummyCheck(BaseCheck):
        def run(self) -> CheckResult:
            return CheckResult(name=self.name, passed=True, message="ok")

    register("dummy", _DummyCheck)
    assert get("dummy") is _DummyCheck
    # Cleanup
    del _REGISTRY["dummy"]


def test_register_rejects_non_basecheck():
    with pytest.raises(TypeError):
        register("bad", object)  # type: ignore


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------

def test_build_check_threshold():
    cfg = CheckConfig(name="my_threshold", check_type="threshold", params={"value": 5.0, "min_val": 1.0, "max_val": 10.0})
    check = build_check(cfg)
    assert isinstance(check, ThresholdCheck)
    assert check.name == "my_threshold"


def test_build_check_unknown_type_raises():
    cfg = CheckConfig(name="bad", check_type="nonexistent", params={})
    with pytest.raises(CheckBuildError, match="nonexistent"):
        build_check(cfg)


def test_build_check_bad_params_raises():
    cfg = CheckConfig(name="bad_params", check_type="threshold", params={"unexpected_kwarg": 99})
    with pytest.raises(CheckBuildError, match="bad_params"):
        build_check(cfg)


def test_build_checks_returns_list():
    configs = [
        CheckConfig(name="c1", check_type="threshold", params={"value": 3.0}),
        CheckConfig(name="c2", check_type="threshold", params={"value": 7.0, "max_val": 10.0}),
    ]
    checks = build_checks(configs)
    assert len(checks) == 2
    assert all(isinstance(c, ThresholdCheck) for c in checks)


def test_build_checks_propagates_error():
    configs = [
        CheckConfig(name="ok", check_type="threshold", params={"value": 1.0}),
        CheckConfig(name="bad", check_type="ghost", params={}),
    ]
    with pytest.raises(CheckBuildError):
        build_checks(configs)
