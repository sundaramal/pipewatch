"""Factory helper for building TimedCheck instances from param dicts."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.timed import TimedCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_timed_from_params(params: Dict[str, Any]) -> TimedCheck:
    """Build a :class:`TimedCheck` from a parameter dictionary.

    Expected keys:
        check (dict): single check definition with ``type`` and optional ``params``.
        max_seconds (float, optional): wall-clock limit before forcing failure.
        name (str, optional): override the auto-generated name.

    Raises:
        CheckBuildError: if ``check`` key is missing or malformed.
    """
    if "check" not in params:
        raise CheckBuildError("TimedCheck requires a 'check' key in params")

    check_def = params["check"]
    if not isinstance(check_def, dict) or "type" not in check_def:
        raise CheckBuildError("'check' must be a dict with a 'type' key")

    wrapped = build_check(check_def["type"], check_def.get("params", {}))
    max_seconds = params.get("max_seconds")
    name = params.get("name")

    return TimedCheck(wrapped=wrapped, max_seconds=max_seconds, name=name)
