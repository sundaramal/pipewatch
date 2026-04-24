"""Tests for build_quarantined_from_params factory helper."""
from __future__ import annotations

import pytest

from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.quarantined import QuarantinedCheck
from pipewatch.checks.quarantined_factory import build_quarantined_from_params
from pipewatch.checks.registry import register_builtins


def _ensure_builtins() -> None:
    try:
        register_builtins()
    except Exception:
        pass


def test_build_returns_quarantined_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "metric": 5, "min": 0, "max": 10},
        "quarantine_seconds": 120,
    }
    result = build_quarantined_from_params(params)
    assert isinstance(result, QuarantinedCheck)


def test_build_respects_quarantine_seconds():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "metric": 5, "min": 0, "max": 10},
        "quarantine_seconds": 90,
    }
    q = build_quarantined_from_params(params)
    assert q.quarantine_seconds == 90.0


def test_build_uses_default_quarantine_seconds():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "metric": 5, "min": 0, "max": 10},
    }
    q = build_quarantined_from_params(params)
    assert q.quarantine_seconds == 60.0


def test_build_respects_custom_name():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "metric": 5, "min": 0, "max": 10},
        "name": "my-quarantined",
    }
    q = build_quarantined_from_params(params)
    assert q.name == "my-quarantined"


def test_build_raises_without_check_key():
    with pytest.raises(CheckBuildError, match="requires a 'check' key"):
        build_quarantined_from_params({"quarantine_seconds": 30})


def test_build_raises_for_invalid_check_cfg():
    with pytest.raises(CheckBuildError):
        build_quarantined_from_params({"check": "not-a-dict"})


def test_build_raises_for_check_cfg_missing_type():
    with pytest.raises(CheckBuildError):
        build_quarantined_from_params({"check": {"metric": 5}})
