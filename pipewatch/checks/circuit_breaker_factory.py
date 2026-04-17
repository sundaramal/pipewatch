"""Factory helper to build a CircuitBreakerCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.circuit_breaker import CircuitBreakerCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_circuit_breaker_from_params(params: Dict[str, Any]) -> CircuitBreakerCheck:
    """Build a :class:`CircuitBreakerCheck` from a parameter dictionary.

    Expected keys:
    - ``check`` (dict): config for the inner check (required).
    - ``threshold`` (int): consecutive failures before opening (default 3).
    - ``reset_timeout`` (float): seconds before attempting reset (default 60).
    - ``name`` (str): optional name override.
    """
    if "check" not in params:
        raise CheckBuildError("circuit_breaker requires a 'check' key")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict):
        raise CheckBuildError("'check' must be a dict describing the inner check")

    inner_type = inner_cfg.get("type")
    if not inner_type:
        raise CheckBuildError("inner 'check' dict must have a 'type' key")

    inner = build_check(inner_type, inner_cfg.get("params", {}))

    threshold = int(params.get("threshold", 3))
    reset_timeout = float(params.get("reset_timeout", 60.0))
    name = params.get("name")

    return CircuitBreakerCheck(
        wrapped=inner,
        threshold=threshold,
        reset_timeout=reset_timeout,
        name=name,
    )
