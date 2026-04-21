"""Factory helper for building a RetryingFallbackCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.retrying_fallback import RetryingFallbackCheck


def build_retrying_fallback_from_params(
    params: Dict[str, Any],
    build_check_fn,  # callable(cfg: dict) -> BaseCheck
) -> RetryingFallbackCheck:
    """Construct a :class:`RetryingFallbackCheck` from a raw params dictionary.

    Expected keys
    -------------
    check     : dict  — config for the primary (wrapped) check  [required]
    fallback  : dict  — config for the fallback check           [required]
    retries   : int   — number of attempts (default 3)
    delay     : float — seconds between retries (default 0.0)
    name      : str   — optional name override
    """
    if "check" not in params:
        raise ValueError("RetryingFallbackCheck requires a 'check' key in params")
    if "fallback" not in params:
        raise ValueError("RetryingFallbackCheck requires a 'fallback' key in params")

    check_cfg = params["check"]
    fallback_cfg = params["fallback"]

    if not isinstance(check_cfg, dict):
        raise TypeError("'check' must be a dict")
    if not isinstance(fallback_cfg, dict):
        raise TypeError("'fallback' must be a dict")

    wrapped = build_check_fn(check_cfg)
    fallback = build_check_fn(fallback_cfg)

    retries = int(params.get("retries", 3))
    delay = float(params.get("delay", 0.0))
    name = params.get("name", None)

    return RetryingFallbackCheck(
        wrapped=wrapped,
        fallback=fallback,
        retries=retries,
        delay=delay,
        name=name,
    )
