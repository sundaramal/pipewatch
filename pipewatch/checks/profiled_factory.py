"""Factory helper for building a ProfiledCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.profiled import ProfiledCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_profiled_from_params(params: Dict[str, Any]) -> ProfiledCheck:
    """Build a :class:`ProfiledCheck` from a configuration parameter dict.

    Expected keys
    -------------
    check : dict
        A single check-config dict with at least a ``type`` key describing
        the inner check to wrap.
    name : str, optional
        Override the auto-generated name for the profiled wrapper.

    Raises
    ------
    CheckBuildError
        If ``check`` is missing, not a dict, or the inner check cannot be built.
    """
    if "check" not in params:
        raise CheckBuildError("ProfiledCheck requires a 'check' key in params")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict):
        raise CheckBuildError("ProfiledCheck 'check' param must be a dict")

    try:
        inner = build_check(inner_cfg)
    except Exception as exc:  # pragma: no cover
        raise CheckBuildError(f"Failed to build inner check for ProfiledCheck: {exc}") from exc

    name: str | None = params.get("name")
    return ProfiledCheck(wrapped=inner, name=name)
