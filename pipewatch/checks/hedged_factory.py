"""Factory helper for building a HedgedCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.hedged import HedgedCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_hedged_from_params(params: Dict[str, Any]) -> HedgedCheck:
    """Construct a :class:`HedgedCheck` from a plain params dictionary.

    Expected keys:
        primary   (dict)  – check config for the primary check.
        secondary (dict)  – check config for the hedge check.
        hedge_after (float, optional) – seconds before launching hedge (default 1.0).
        name (str, optional) – display name.

    Raises:
        CheckBuildError: if *primary* or *secondary* keys are missing or invalid.
    """
    if "primary" not in params:
        raise CheckBuildError("hedged: 'primary' key is required")
    if "secondary" not in params:
        raise CheckBuildError("hedged: 'secondary' key is required")

    primary_cfg = params["primary"]
    secondary_cfg = params["secondary"]

    if not isinstance(primary_cfg, dict):
        raise CheckBuildError("hedged: 'primary' must be a dict check config")
    if not isinstance(secondary_cfg, dict):
        raise CheckBuildError("hedged: 'secondary' must be a dict check config")

    primary = build_check(primary_cfg)
    secondary = build_check(secondary_cfg)

    hedge_after = float(params.get("hedge_after", 1.0))
    name = params.get("name", None)

    return HedgedCheck(
        primary=primary,
        secondary=secondary,
        hedge_after=hedge_after,
        name=name,
    )
