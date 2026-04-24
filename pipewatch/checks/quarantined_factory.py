"""Factory helper for building a QuarantinedCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.quarantined import QuarantinedCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_quarantined_from_params(params: Dict[str, Any]) -> QuarantinedCheck:
    """Build a :class:`QuarantinedCheck` from a raw params dictionary.

    Expected keys
    -------------
    check : dict
        A single check-config dict with at least a ``type`` key.
    quarantine_seconds : float, optional
        How long to suppress the check after a failure (default: 60).
    name : str, optional
        Override the auto-generated name.

    Raises
    ------
    CheckBuildError
        If the ``check`` key is missing or invalid.
    """
    if "check" not in params:
        raise CheckBuildError("quarantined check requires a 'check' key in params")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict) or "type" not in inner_cfg:
        raise CheckBuildError(
            "'check' must be a dict with at least a 'type' key"
        )

    inner = build_check(
        check_type=inner_cfg["type"],
        name=inner_cfg.get("name"),
        params={k: v for k, v in inner_cfg.items() if k not in ("type", "name")},
    )

    return QuarantinedCheck(
        check=inner,
        quarantine_seconds=float(params.get("quarantine_seconds", 60.0)),
        name=params.get("name"),
    )
