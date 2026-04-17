"""Tests for build_chained_from_params helper."""
import pytest
from pipewatch.checks.registry import register_builtins
from pipewatch.checks.chained import ChainedCheck
from pipewatch.checks.chained_factory import build_chained_from_params
from pipewatch.checks.factory import CheckBuildError

register_builtins()


def test_build_chained_returns_chained_instance():
    params = {
        "checks": [
            {"type": "threshold", "name": "rows", "params": {"min": 0}},
        ]
    }
    c = build_chained_from_params("my_chain", params)
    assert isinstance(c, ChainedCheck)
    assert c.name == "my_chain"


def test_build_chained_has_correct_number_of_steps():
    params = {
        "checks": [
            {"type": "threshold", "name": "a", "params": {"min": 0}},
            {"type": "threshold", "name": "b", "params": {"max": 100}},
        ]
    }
    c = build_chained_from_params("chain", params)
    assert len(c.checks) == 2


def test_build_chained_raises_without_checks_key():
    with pytest.raises(CheckBuildError, match="requires a non-empty"):
        build_chained_from_params("chain", {})


def test_build_chained_raises_with_empty_checks_list():
    with pytest.raises(CheckBuildError, match="requires a non-empty"):
        build_chained_from_params("chain", {"checks": []})


def test_build_chained_raises_for_non_dict_entry():
    with pytest.raises(CheckBuildError, match="must be a dict"):
        build_chained_from_params("chain", {"checks": ["bad"]})


def test_build_chained_raises_for_missing_type():
    with pytest.raises(CheckBuildError, match="missing 'type'"):
        build_chained_from_params("chain", {"checks": [{"name": "x"}]})


def test_build_chained_run_passes_for_valid_thresholds():
    params = {
        "checks": [
            {"type": "threshold", "name": "low", "params": {"value": 5, "min": 1}},
        ]
    }
    c = build_chained_from_params("chain", params)
    result = c.run()
    assert result.passed
