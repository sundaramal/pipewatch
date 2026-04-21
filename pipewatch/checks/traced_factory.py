"""Factory helper for building a :class:`TracedCheck` from a params dict."""

from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.traced import TracedCheck
from pipewatch.checks.registry import get
from pipewatch.checks.factory import CheckBuildError


def build_traced_from_params(params: Dict[str, Any]) -> TracedCheck:
    """Build a :class:`TracedCheck` from a raw params dictionary.

    Expected keys
    -------------
    check : dict
        A single check config dict with ``type`` and optional ``params``.
    max_entries : int, optional
        Maximum number of trace entries to retain (default 100).
    name : str, optional
        Override for the check name.

    Raises
    ------
    CheckBuildError
        If required keys are missing or the inner check cannot be built.
    """
    if "check" not in params:
        raise CheckBuildError("TracedCheck requires a 'check' key in params")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict) or "type" not in inner_cfg:
        raise CheckBuildError(
            "TracedCheck 'check' must be a dict with a 'type' key"
        )

    inner_cls = get(inner_cfg["type"])
    inner_params = inner_cfg.get("params", {})
    inner = inner_cls(**inner_params)

    max_entries = params.get("max_entries", 100)
    name = params.get("name", None)

    return TracedCheck(inner, max_entries=max_entries, name=name)
