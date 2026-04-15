"""Configuration loader for pipewatch pipeline check definitions."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when a configuration file is invalid or missing required fields."""


@dataclass
class CheckConfig:
    """Parsed configuration for a single check."""

    name: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ConfigError("Check 'name' must be a non-empty string.")
        if not self.type:
            raise ConfigError("Check 'type' must be a non-empty string.")


@dataclass
class PipelineConfig:
    """Top-level configuration for a pipeline."""

    pipeline: str
    checks: list[CheckConfig] = field(default_factory=list)

    def get_check(self, name: str) -> CheckConfig | None:
        """Return the first check with the given name, or None if not found."""
        return next((c for c in self.checks if c.name == name), None)


def load_config(path: str | Path) -> PipelineConfig:
    """Load and validate a YAML pipeline configuration file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A :class:`PipelineConfig` instance.

    Raises:
        ConfigError: If the file is missing required fields or is malformed.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config file must contain a YAML mapping at the top level.")

    pipeline_name = raw.get("pipeline")
    if not pipeline_name:
        raise ConfigError("Config must include a 'pipeline' name.")

    raw_checks = raw.get("checks", [])
    if not isinstance(raw_checks, list):
        raise ConfigError("'checks' must be a list.")

    checks: list[CheckConfig] = []
    for i, item in enumerate(raw_checks):
        if not isinstance(item, dict):
            raise ConfigError(f"Check at index {i} must be a mapping.")
        try:
            checks.append(
                CheckConfig(
                    name=item.get("name", ""),
                    type=item.get("type", ""),
                    params={k: v for k, v in item.items() if k not in ("name", "type")},
                )
            )
        except ConfigError as exc:
            raise ConfigError(f"Check at index {i}: {exc}") from exc

    return PipelineConfig(pipeline=pipeline_name, checks=checks)
