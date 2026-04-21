"""Factory helper for building EveryCheck instances from parameter dicts.

This module provides `build_every_from_params`, which constructs an
EveryCheck from a nested configuration dictionary, delegating sub-check
construction to the registry-based `build_check` factory.
"""

from __future__ import annotations

from typing import Any

from pipewatch.checks.every import EveryCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_every_from_params(params: dict[str, Any]) -> EveryCheck:
    """Build an EveryCheck from a parameter dictionary.

    Expected params structure::

        {
            "checks": [
                {"type": "threshold", "params": {"min": 0}},
                {"type": "freshness", "params": {"max_age_seconds": 300}},
            ],
            "name": "my_every_check",   # optional
        }

    Args:
        params: A dict containing at least a ``checks`` key whose value is a
            non-empty list of sub-check configuration dicts.  An optional
            ``name`` key may be provided for the composite check.

    Returns:
        A fully-constructed :class:`~pipewatch.checks.every.EveryCheck`.

    Raises:
        CheckBuildError: If ``checks`` is missing, empty, or contains invalid
            entries.
    """
    if "checks" not in params:
        raise CheckBuildError(
            "EveryCheck requires a 'checks' key in params"
        )

    sub_check_cfgs = params["checks"]

    if not sub_check_cfgs:
        raise CheckBuildError(
            "EveryCheck 'checks' list must not be empty"
        )

    name: str | None = params.get("name")
    every = EveryCheck(name=name)

    for idx, cfg in enumerate(sub_check_cfgs):
        if not isinstance(cfg, dict):
            raise CheckBuildError(
                f"EveryCheck sub-check at index {idx} must be a dict, "
                f"got {type(cfg).__name__!r}"
            )
        if "type" not in cfg:
            raise CheckBuildError(
                f"EveryCheck sub-check at index {idx} is missing 'type' key"
            )

        sub_check = build_check(
            check_type=cfg["type"],
            name=cfg.get("name", f"{name or 'every'}_step_{idx}"),
            params=cfg.get("params", {}),
        )
        every.add_check(sub_check)

    return every
