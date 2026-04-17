"""Tests for build_circuit_breaker_from_params."""
from __future__ import annotations

import pytest

from pipewatch.checks.circuit_breaker import CircuitBreakerCheck
from pipewatch.checks.circuit_breaker_factory import build_circuit_breaker_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks import registry


def _ensure_builtins():
    registry.register_builtins()


def test_build_returns_circuit_breaker_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "threshold": 2,
        "reset_timeout": 30,
    }
    cb = build_circuit_breaker_from_params(params)
    assert isinstance(cb, CircuitBreakerCheck)


def test_build_respects_threshold():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "threshold": 5,
    }
    cb = build_circuit_breaker_from_params(params)
    assert cb.threshold == 5


def test_build_respects_reset_timeout():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "reset_timeout": 120,
    }
    cb = build_circuit_breaker_from_params(params)
    assert cb.reset_timeout == 120.0


def test_build_raises_without_check_key():
    with pytest.raises(CheckBuildError, match="requires a 'check' key"):
        build_circuit_breaker_from_params({"threshold": 3})


def test_build_raises_when_check_not_dict():
    with pytest.raises(CheckBuildError, match="must be a dict"):
        build_circuit_breaker_from_params({"check": "threshold"})


def test_build_raises_when_inner_missing_type():
    with pytest.raises(CheckBuildError, match="must have a 'type' key"):
        build_circuit_breaker_from_params({"check": {"params": {}}})


def test_build_custom_name():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "name": "my_breaker",
    }
    cb = build_circuit_breaker_from_params(params)
    assert cb.name == "my_breaker"
