"""Factory helper for building a BouncedCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.bounced import BouncedCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_bounced_from_params(params: Dict[str, Any]) -> BouncedCheck:
    """Construct a :class:`BouncedCheck` from a raw params dictionary.

    Expected keys
    -------------
    check : dict
        A single check config dict with ``type`` and optional ``params``.
    gap_seconds : float
        Minimum seconds between executions.  Defaults to ``1.0``.
    name : str, optional
        Override display name.

    Raises
    ------
    CheckBuildError
        If *check* key is missing or the inner check cannot be built.
    """
    if "check" not in params:
        raise CheckBuildError("BouncedCheck requires a 'check' key in params")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict) or "type" not in inner_cfg:
        raise CheckBuildError(
            "'check' must be a dict with at least a 'type' key"
        )

    inner = build_check(
        check_type=inner_cfg["type"],
        name=inner_cfg.get("name"),
        params=inner_cfg.get("params", {}),
    )

    gap_seconds: float = float(params.get("gap_seconds", 1.0))
    name: str | None = params.get("name")

    return BouncedCheck(check=inner, gap_seconds=gap_seconds, name=name)
