"""Factory helper to build FallbackCheck from config dict."""

from __future__ import annotations
from typing import Any

from pipewatch.checks.base import BaseCheck
from pipewatch.checks.fallback import FallbackCheck


def build_fallback_from_params(params: dict[str, Any], build_fn) -> FallbackCheck:
    """Construct a FallbackCheck from a params dict.

    Expected params keys:
      - primary: dict with 'type' and optional params
      - fallback: dict with 'type' and optional params
      - name: optional str
    """
    if "primary" not in params:
        raise ValueError("FallbackCheck requires 'primary' in params")
    if "fallback" not in params:
        raise ValueError("FallbackCheck requires 'fallback' in params")

    primary_cfg = params["primary"]
    fallback_cfg = params["fallback"]

    primary: BaseCheck = build_fn(
        primary_cfg["type"], primary_cfg.get("params", {})
    )
    fallback: BaseCheck = build_fn(
        fallback_cfg["type"], fallback_cfg.get("params", {})
    )

    name = params.get("name", "fallback")
    return FallbackCheck(primary=primary, fallback=fallback, name=name)
