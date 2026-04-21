"""Factory helper for building a :class:`ClampedCheck` from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.clamped import ClampedCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_clamped_from_params(params: Dict[str, Any]) -> ClampedCheck:
    """Build a :class:`ClampedCheck` from a raw params dictionary.

    Expected keys
    -------------
    check   : dict  – config for the inner check (required).
    min_val : float – lower clamp bound (optional).
    max_val : float – upper clamp bound (optional).
    name    : str   – display name override (optional).

    Raises
    ------
    CheckBuildError
        If the ``check`` key is missing or the inner check cannot be built.
    """
    if "check" not in params:
        raise CheckBuildError("clamped requires a 'check' key in params")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict):
        raise CheckBuildError("clamped 'check' param must be a dict")

    check_type = inner_cfg.get("type")
    if not check_type:
        raise CheckBuildError("inner check config must include a 'type' key")

    inner = build_check(check_type, inner_cfg.get("params", {}))

    min_val = params.get("min_val")
    max_val = params.get("max_val")
    name = params.get("name")

    try:
        return ClampedCheck(
            wrapped=inner,
            min_val=float(min_val) if min_val is not None else None,
            max_val=float(max_val) if max_val is not None else None,
            name=name,
        )
    except ValueError as exc:
        raise CheckBuildError(str(exc)) from exc
