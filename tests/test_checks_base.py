"""Tests for pipewatch.checks.base — CheckResult, BaseCheck, and registry."""

import pytest

from pipewatch.checks.base import (
    BaseCheck,
    CheckResult,
    get_check_class,
    list_checks,
    register_check,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@register_check
class _AlwaysPassCheck(BaseCheck):
    name = "always_pass"

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="All good")


@register_check
class _AlwaysFailCheck(BaseCheck):
    name = "always_fail"

    def run(self) -> CheckResult:
        return CheckResult(
            name=self.name,
            passed=False,
            message="Something broke",
            details={"code": 42},
        )


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------


def test_check_result_str_pass():
    result = CheckResult(name="my_check", passed=True, message="ok")
    assert str(result) == "[PASS] my_check: ok"


def test_check_result_str_fail():
    result = CheckResult(name="my_check", passed=False, message="oops")
    assert str(result) == "[FAIL] my_check: oops"


def test_check_result_details_default_none():
    result = CheckResult(name="x", passed=True, message="y")
    assert result.details is None


# ---------------------------------------------------------------------------
# BaseCheck
# ---------------------------------------------------------------------------


def test_cannot_instantiate_base_check_directly():
    with pytest.raises(TypeError):
        BaseCheck(config={})  # type: ignore[abstract]


def test_always_pass_check_runs():
    check = _AlwaysPassCheck(config={})
    result = check.run()
    assert result.passed is True
    assert result.name == "always_pass"


def test_always_fail_check_runs():
    check = _AlwaysFailCheck(config={"threshold": 10})
    result = check.run()
    assert result.passed is False
    assert result.details == {"code": 42}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registered_checks_are_retrievable():
    assert get_check_class("always_pass") is _AlwaysPassCheck
    assert get_check_class("always_fail") is _AlwaysFailCheck


def test_unknown_check_raises_key_error():
    with pytest.raises(KeyError, match="Unknown check type 'nonexistent'"):
        get_check_class("nonexistent")


def test_list_checks_returns_copy():
    checks = list_checks()
    assert "always_pass" in checks
    checks["injected"] = object()  # mutating the copy should not affect registry
    assert "injected" not in list_checks()


def test_register_check_rejects_non_subclass():
    with pytest.raises(TypeError):

        @register_check
        class _Bad:
            name = "bad"
