"""Tests for pipewatch.config module."""

import pytest
from pathlib import Path

from pipewatch.config import load_config, CheckConfig, PipelineConfig, ConfigError


VALID_YAML = """\
pipeline: my_pipeline
checks:
  - name: row_count
    type: threshold
    min: 100
    max: 10000
  - name: freshness
    type: freshness
    max_age_seconds: 3600
"""


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    f = tmp_path / "pipeline.yaml"
    f.write_text(VALID_YAML)
    return f


def test_load_config_returns_pipeline_config(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert isinstance(cfg, PipelineConfig)
    assert cfg.pipeline == "my_pipeline"


def test_load_config_parses_checks(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert len(cfg.checks) == 2
    assert all(isinstance(c, CheckConfig) for c in cfg.checks)


def test_load_config_check_names_and_types(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.checks[0].name == "row_count"
    assert cfg.checks[0].type == "threshold"
    assert cfg.checks[1].name == "freshness"
    assert cfg.checks[1].type == "freshness"


def test_load_config_check_params(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.checks[0].params == {"min": 100, "max": 10000}
    assert cfg.checks[1].params == {"max_age_seconds": 3600}


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nonexistent.yaml")


def test_load_config_missing_pipeline_key_raises(tmp_path: Path) -> None:
    f = tmp_path / "bad.yaml"
    f.write_text("checks: []\n")
    with pytest.raises(ConfigError, match="pipeline"):
        load_config(f)


def test_load_config_invalid_yaml_raises(tmp_path: Path) -> None:
    f = tmp_path / "bad.yaml"
    f.write_text(": : invalid: yaml: [\n")
    with pytest.raises(ConfigError, match="Failed to parse"):
        load_config(f)


def test_load_config_check_missing_name_raises(tmp_path: Path) -> None:
    f = tmp_path / "bad.yaml"
    f.write_text("pipeline: p\nchecks:\n  - type: threshold\n")
    with pytest.raises(ConfigError, match="name"):
        load_config(f)


def test_load_config_check_missing_type_raises(tmp_path: Path) -> None:
    f = tmp_path / "bad.yaml"
    f.write_text("pipeline: p\nchecks:\n  - name: my_check\n")
    with pytest.raises(ConfigError, match="type"):
        load_config(f)


def test_load_config_empty_checks_list(tmp_path: Path) -> None:
    f = tmp_path / "empty.yaml"
    f.write_text("pipeline: empty_pipeline\nchecks: []\n")
    cfg = load_config(f)
    assert cfg.pipeline == "empty_pipeline"
    assert cfg.checks == []
