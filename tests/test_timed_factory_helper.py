"""Tests for build_timed_from_params."""
from __future__ import annotations

import pytest

from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.timed import TimedCheck
from pipewatch.checks.timed_factory import build_timed_from_params
from pipewatch.checks.registry import register_builtins


def _ensure_builtins():
    try:
        register_builtins()
    except Exception:
        pass


def test_build_returns_timed_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}}
    }
    result = build_timed_from_params(params)
    assert isinstance(result, TimedCheck)


def test_build_respects_max_seconds():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "max_seconds": 2.5,
    }
    check = build_timed_from_params(params)
    assert check._max_seconds == 2.5


def test_build_respects_custom_name():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "name": "custom_timed",
    }
    check = build_timed_from_params(params)
    assert check.name == "custom_timed"


def test_build_raises_without_check_key():
    with pytest.raises(CheckBuildError, match="requires a 'check' key"):
        build_timed_from_params({})


def test_build_raises_for_non_dict_check():
    with pytest.raises(CheckBuildError):
        build_timed_from_params({"check": "threshold"})


def test_build_raises_for_check_missing_type():
    with pytest.raises(CheckBuildError):
        build_timed_from_params({"check": {"params": {}}})


def test_build_without_max_seconds_defaults_to_none():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 3, "min": 1, "max": 10}}
    }
    check = build_timed_from_params(params)
    assert check._max_seconds is None
