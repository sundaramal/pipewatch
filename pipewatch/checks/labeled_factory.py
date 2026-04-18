"""Factory helper for building LabeledCheck from config params."""
from __future__ import annotations
from pipewatch.checks.labeled import LabeledCheck
from pipewatch.checks import registry


def build_labeled_from_params(params: dict) -> LabeledCheck:
    """Build a LabeledCheck from a params dict.

    Expected keys:
        check (dict): sub-check config with 'type' and optional 'params'.
        labels (dict): key/value labels to attach.
        name (str, optional): override name.
    """
    if "check" not in params:
        raise ValueError("LabeledCheck requires a 'check' key in params")

    check_cfg = params["check"]
    if not isinstance(check_cfg, dict) or "type" not in check_cfg:
        raise ValueError("'check' must be a dict with a 'type' key")

    cls = registry.get(check_cfg["type"])
    sub_params = check_cfg.get("params", {})
    sub_check = cls(**sub_params) if sub_params else cls()

    labels = params.get("labels", {})
    name = params.get("name")
    return LabeledCheck(wrapped=sub_check, labels=labels, name=name)
