"""Tests for build_labeled_from_params."""
import pytest
from pipewatch.checks.labeled import LabeledCheck
from pipewatch.checks.labeled_factory import build_labeled_from_params
from pipewatch.checks import registry


def _ensure_builtins():
    registry.register_builtins()


def test_build_returns_labeled_instance():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 0, "max": 10}},
        "labels": {"env": "test"},
    }
    result = build_labeled_from_params(params)
    assert isinstance(result, LabeledCheck)


def test_build_labels_are_set():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 0, "max": 10}},
        "labels": {"region": "us-east"},
    }
    check = build_labeled_from_params(params)
    assert check.labels == {"region": "us-east"}


def test_build_raises_without_check_key():
    with pytest.raises(ValueError, match="requires a 'check' key"):
        build_labeled_from_params({"labels": {"x": "1"}})


def test_build_raises_for_invalid_check_cfg():
    with pytest.raises(ValueError, match="'check' must be a dict"):
        build_labeled_from_params({"check": "not_a_dict"})


def test_build_raises_for_check_missing_type():
    with pytest.raises(ValueError, match="'check' must be a dict with a 'type' key"):
        build_labeled_from_params({"check": {"params": {}}})


def test_build_custom_name():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 0, "max": 10}},
        "name": "my_labeled",
    }
    check = build_labeled_from_params(params)
    assert check.name == "my_labeled"


def test_build_result_passes_for_valid_threshold():
    _ensure_builtins()
    params = {
        "check": {"type": "threshold", "params": {"value": 5, "min": 0, "max": 10}},
        "labels": {"env": "ci"},
    }
    check = build_labeled_from_params(params)
    result = check.run()
    assert result.passed is True
    assert "env=ci" in result.message
