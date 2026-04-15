"""Parse alert handler configuration and instantiate alerters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from pipewatch.alerts import BaseAlerter, EmailAlerter, LogAlerter
from pipewatch.config import ConfigError

_ALERTER_REGISTRY: Dict[str, type] = {
    "log": LogAlerter,
    "email": EmailAlerter,
}


@dataclass
class AlertConfig:
    """Raw configuration for a single alert handler."""

    type: str
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in _ALERTER_REGISTRY:
            raise ConfigError(
                f"Unknown alert type '{self.type}'. "
                f"Available types: {sorted(_ALERTER_REGISTRY)}"
            )


def build_alerter(config: AlertConfig) -> BaseAlerter:
    """Instantiate an alerter from an AlertConfig."""
    cls = _ALERTER_REGISTRY[config.type]
    try:
        return cls(**config.params)
    except TypeError as exc:
        raise ConfigError(
            f"Invalid params for alert type '{config.type}': {exc}"
        ) from exc


def load_alerters(raw: List[Dict[str, Any]]) -> List[BaseAlerter]:
    """Parse a list of raw alert dicts (from YAML/JSON) into alerter instances.

    Each entry must have a ``type`` key and an optional ``params`` mapping.

    Example YAML::

        alerts:
          - type: log
            params:
              level: ERROR
          - type: email
            params:
              recipients:
                - ops@example.com
    """
    alerters: List[BaseAlerter] = []
    for entry in raw:
        if "type" not in entry:
            raise ConfigError("Each alert entry must have a 'type' field.")
        cfg = AlertConfig(
            type=entry["type"],
            params=entry.get("params", {}),
        )
        alerters.append(build_alerter(cfg))
    return alerters
