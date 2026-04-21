"""Tests for build_traced_from_params factory helper."""

from __future__ import annotations

import pytest

from pipewatch.checks.registry import register_builtins
from pipewatch.checks.traced import TracedCheck
from pipewatch.checks.traced_factory import build_traced_from_params
from pipewatch.checks.factory import CheckBuildError


def _ensure_builtins() -> None:
    register_builtins()


def test_build_returns_traced_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}}
    }
    result = build_traced_from_params(params)
    assert isinstance(result, TracedCheck)


def test_build_respects_max_entries():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "max_entries": 7,
    }
    tc = build_traced_from_params(params)
    assert tc._max_entries == 7


def test_build_respects_custom_name():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}},
        "name": "my_trace",
    }
    tc = build_traced_from_params(params)
    assert tc.name == "my_trace"


def test_build_raises_without_check_key():
    with pytest.raises(CheckBuildError, match="requires a 'check' key"):
        build_traced_from_params({})


def test_build_raises_for_invalid_check_cfg():
    with pytest.raises(CheckBuildError, match="must be a dict with a 'type' key"):
        build_traced_from_params({"check": "not-a-dict"})


def test_build_raises_for_check_cfg_missing_type():
    with pytest.raises(CheckBuildError, match="must be a dict with a 'type' key"):
        build_traced_from_params({"check": {"params": {}}})


def test_built_check_records_trace_on_run():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 1, "max": 10}}
    }
    tc = build_traced_from_params(params)
    tc.run()
    assert len(tc.trace) == 1
    assert tc.trace[0].passed is True
