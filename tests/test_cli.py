"""Tests for the pipewatch CLI."""

import textwrap
import pytest
from click.testing import CliRunner

from pipewatch.cli import main


@pytest.fixture()
def passing_config(tmp_path):
    cfg = tmp_path / "pipeline.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            name: test-pipeline
            checks:
              - name: value_ok
                type: threshold
                params:
                  value: 50
                  min: 0
                  max: 100
        """)
    )
    return str(cfg)


@pytest.fixture()
def failing_config(tmp_path):
    cfg = tmp_path / "pipeline.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            name: test-pipeline
            checks:
              - name: value_bad
                type: threshold
                params:
                  value: 200
                  min: 0
                  max: 100
        """)
    )
    return str(cfg)


@pytest.fixture()
def unknown_type_config(tmp_path):
    cfg = tmp_path / "pipeline.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            name: test-pipeline
            checks:
              - name: mystery
                type: nonexistent_check
                params: {}
        """)
    )
    return str(cfg)


def test_cli_exits_zero_when_all_pass(passing_config):
    runner = CliRunner()
    result = runner.invoke(main, [passing_config])
    assert result.exit_code == 0


def test_cli_exits_one_when_failures(failing_config):
    runner = CliRunner()
    result = runner.invoke(main, [failing_config])
    assert result.exit_code == 1


def test_cli_output_contains_pipeline_name(passing_config):
    runner = CliRunner()
    result = runner.invoke(main, [passing_config])
    assert "test-pipeline" in result.output


def test_cli_verbose_shows_check_results(passing_config):
    runner = CliRunner()
    result = runner.invoke(main, [passing_config, "--verbose"])
    assert "value_ok" in result.output


def test_cli_unknown_check_type_exits_two(unknown_type_config):
    runner = CliRunner()
    result = runner.invoke(main, [unknown_type_config])
    assert result.exit_code == 2
    assert "nonexistent_check" in result.output
