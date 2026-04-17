"""Tests for build_parallel_from_params."""
from __future__ import annotations

import pytest
from pipewatch.checks.parallel import ParallelCheck
from pipewatch.checks.parallel_factory import build_parallel_from_params
from pipewatch.checks.factory import CheckBuildError
from pipewatch.checks.registry import register_builtins

register_builtins()


def test_build_parallel_returns_parallel_instance():
    params = {
        "checks": [
            {"type": "threshold", "name": "t1", "params": {"value": 5, "min": 0, "max": 10}}
        ]
    }
    result = build_parallel_from_params("my_parallel", params)
    assert isinstance(result, ParallelCheck)


def test_build_parallel_correct_sub_check_count():
    params = {
        "checks": [
            {"type": "threshold", "name": "a", "params": {"value": 1}},
            {"type": "threshold", "name": "b", "params": {"value": 2}},
        ]
    }
    pc = build_parallel_from_params("p", params)
    assert len(pc.checks) == 2


def test_build_parallel_raises_without_checks_key():
    with pytest.raises(CheckBuildError):
        build_parallel_from_params("p", {})


def test_build_parallel_raises_with_empty_checks_list():
    with pytest.raises(CheckBuildError):
        build_parallel_from_params("p", {"checks": []})


def test_build_parallel_raises_for_non_dict_entry():
    with pytest.raises(CheckBuildError):
        build_parallel_from_params("p", {"checks": ["not_a_dict"]})


def test_build_parallel_raises_for_missing_type():
    with pytest.raises(CheckBuildError):
        build_parallel_from_params("p", {"checks": [{"name": "x"}]})


def test_build_parallel_default_sub_name():
    params = {
        "checks": [
            {"type": "threshold", "params": {"value": 3}}
        ]
    }
    pc = build_parallel_from_params("root", params)
    assert pc.checks[0].name == "root_sub_0"


def test_build_parallel_custom_timeout():
    params = {
        "timeout": 7.5,
        "checks": [
            {"type": "threshold", "name": "t", "params": {"value": 1}}
        ],
    }
    pc = build_parallel_from_params("p", params)
    assert pc._timeout == 7.5
