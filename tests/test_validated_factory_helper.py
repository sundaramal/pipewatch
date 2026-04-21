"""Tests for build_validated_from_params factory helper."""
from __future__ import annotations

import pytest

from pipewatch.checks.registry import register_builtins
from pipewatch.checks.validated import ValidatedCheck
from pipewatch.checks.validated_factory import build_validated_from_params


def _ensure_builtins():
    register_builtins()


def test_build_returns_validated_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
    }
    result = build_validated_from_params(params)
    assert isinstance(result, ValidatedCheck)


def test_build_default_validator_is_require_pass():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
    }
    check = build_validated_from_params(params)
    assert check.run().passed is True


def test_build_require_fail_validator_rejects_passing_inner():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "validator": "require_fail",
    }
    check = build_validated_from_params(params)
    assert check.run().passed is False


def test_build_always_accept_validator():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 999, "max": 10}},
        "validator": "always_accept",
    }
    check = build_validated_from_params(params)
    # inner fails (value > max) but validator accepts everything
    assert check.run().passed is False  # inner result passes through


def test_build_respects_custom_message():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "validator": "require_fail",
        "message": "expected a failure here",
    }
    check = build_validated_from_params(params)
    result = check.run()
    assert "expected a failure here" in result.message


def test_build_respects_custom_name():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "name": "my_validated",
    }
    check = build_validated_from_params(params)
    assert check.name == "my_validated"


def test_build_raises_without_check_key():
    with pytest.raises(ValueError, match="requires a 'check' key"):
        build_validated_from_params({})


def test_build_raises_for_invalid_check_cfg():
    with pytest.raises(ValueError, match="'check' must be a dict"):
        build_validated_from_params({"check": "not-a-dict"})


def test_build_raises_for_unknown_validator():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5}},
        "validator": "nonexistent_validator",
    }
    with pytest.raises(ValueError, match="Unknown validator"):
        build_validated_from_params(params)
