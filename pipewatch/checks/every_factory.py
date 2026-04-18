"""Factory helper for building EveryCheck instances from param dicts."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.every import EveryCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_every_from_params(params: Dict[str, Any]) -> EveryCheck:
    """Construct an :class:`EveryCheck` from a params dict.

    Expected params layout::

        {
            "name": "optional-name",   # optional
            "checks": [                 # required, non-empty list
                {"type": "threshold", ...},
                ...
            ]
        }

    Raises
    ------
    CheckBuildError
        If *checks* key is missing, empty, or contains non-dict entries.
    """
    raw_checks = params.get("checks")
    if not raw_checks:
        raise CheckBuildError("EveryCheck requires a non-empty 'checks' list in params")
    if not isinstance(raw_checks, list):
        raise CheckBuildError("'checks' must be a list of check config dicts")

    name = params.get("name", "every")
    every = EveryCheck(name=name)

    for idx, entry in enumerate(raw_checks):
        if not isinstance(entry, dict):
            raise CheckBuildError(
                f"Each entry in 'checks' must be a dict (got {type(entry)} at index {idx})"
            )
        sub = build_check(entry)
        every.add_check(sub)

    return every
