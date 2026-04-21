"""Factory helper for building ValidatedCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.registry import get
from pipewatch.checks.validated import ValidatedCheck

# Built-in named validators that can be referenced by string in config.
_NAMED_VALIDATORS = {
    "always_accept": lambda r: True,
    "require_pass": lambda r: r.passed,
    "require_fail": lambda r: not r.passed,
    "has_message": lambda r: bool(r.message and r.message.strip()),
}


def build_validated_from_params(params: Dict[str, Any]) -> ValidatedCheck:
    """Construct a :class:`ValidatedCheck` from a plain-dict *params*.

    Expected keys
    -------------
    check : dict
        Mandatory. A ``{type: ..., params: ...}`` dict describing the inner
        check to wrap.
    validator : str
        One of the built-in validator names (default: ``"require_pass"``).
    message : str
        Optional failure message override.
    name : str
        Optional name override.
    """
    if "check" not in params:
        raise ValueError("ValidatedCheck requires a 'check' key in params")

    inner_cfg = params["check"]
    if not isinstance(inner_cfg, dict) or "type" not in inner_cfg:
        raise ValueError("'check' must be a dict with a 'type' key")

    inner_cls = get(inner_cfg["type"])
    inner_check = inner_cls(**(inner_cfg.get("params") or {}))

    validator_name = params.get("validator", "require_pass")
    if validator_name not in _NAMED_VALIDATORS:
        raise ValueError(
            f"Unknown validator '{validator_name}'. "
            f"Available: {sorted(_NAMED_VALIDATORS)}"
        )
    validator = _NAMED_VALIDATORS[validator_name]

    kwargs: Dict[str, Any] = {}
    if "message" in params:
        kwargs["message"] = params["message"]
    if "name" in params:
        kwargs["name"] = params["name"]

    return ValidatedCheck(inner_check, validator, **kwargs)
