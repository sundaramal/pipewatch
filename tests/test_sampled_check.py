"""Tests for SampledCheck."""
from __future__ import annotations

import random
from typing import Optional

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.sampled import SampledCheck


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="always_pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="always_fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="fail")


def _rng_always_run() -> random.Random:
    """Returns a seeded RNG whose first value is <= any rate > 0."""
    rng = random.Random()
    rng.random = lambda: 0.0  # type: ignore[method-assign]
    return rng


def _rng_always_skip() -> random.Random:
    rng = random.Random()
    rng.random = lambda: 1.0  # type: ignore[method-assign]
    return rng


def test_sampled_check_runs_when_rng_below_rate():
    check = SampledCheck(_PassCheck(), rate=0.5, _rng=_rng_always_run())
    result = check.run()
    assert result.passed
    assert "[sampled]" in result.message
    assert "ok" in result.message


def test_sampled_check_skips_when_rng_above_rate():
    check = SampledCheck(_FailCheck(), rate=0.5, _rng=_rng_always_skip())
    result = check.run()
    assert result.passed, "skipped checks should return passing result"
    assert "skipped" in result.message


def test_sampled_check_rate_zero_always_skips():
    check = SampledCheck(_FailCheck(), rate=0.0, _rng=random.Random(42))
    for _ in range(20):
        result = check.run()
        assert result.passed
        assert "skipped" in result.message


def test_sampled_check_rate_one_always_runs():
    check = SampledCheck(_FailCheck(), rate=1.0, _rng=random.Random(42))
    for _ in range(5):
        result = check.run()
        assert not result.passed


def test_sampled_check_invalid_rate_raises():
    with pytest.raises(ValueError, match="rate must be between"):
        SampledCheck(_PassCheck(), rate=1.5)

    with pytest.raises(ValueError, match="rate must be between"):
        SampledCheck(_PassCheck(), rate=-0.1)


def test_sampled_check_default_name():
    check = SampledCheck(_PassCheck(), rate=0.8)
    assert "sampled" in check.name
    assert "always_pass" in check.name


def test_sampled_check_custom_name():
    check = SampledCheck(_PassCheck(), rate=0.5, name="my_sampled")
    assert check.name == "my_sampled"


def test_sampled_check_wrapped_property():
    inner = _PassCheck()
    check = SampledCheck(inner, rate=0.5)
    assert check.wrapped is inner


def test_sampled_check_rate_property():
    check = SampledCheck(_PassCheck(), rate=0.3)
    assert check.rate == pytest.approx(0.3)
