"""Helper to build a ChainedCheck from a params dict."""
from __future__ import annotations
from typing import Any, Dict
from pipewatch.checks.chained import ChainedCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_chained_from_params(name: str, params: Dict[str, Any]) -> ChainedCheck:
    """Build a ChainedCheck from a params dict.

    Expected params::

        checks:
          - type: threshold
            name: row_count
            params: {min: 1}
          - type: freshness
            name: updated_at
            params: {column: updated_at, max_age_seconds: 3600}
    """
    raw_checks = params.get("checks")
    if not raw_checks or not isinstance(raw_checks, list):
        raise CheckBuildError(
            f"ChainedCheck '{name}' requires a non-empty 'checks' list in params"
        )

    inner_checks = []
    for i, entry in enumerate(raw_checks):
        if not isinstance(entry, dict):
            raise CheckBuildError(
                f"ChainedCheck '{name}': entry {i} must be a dict, got {type(entry)}"
            )
        check_type = entry.get("type")
        check_name = entry.get("name", f"{name}_step_{i}")
        check_params = entry.get("params", {})
        if not check_type:
            raise CheckBuildError(
                f"ChainedCheck '{name}': entry {i} missing 'type'"
            )
        inner_checks.append(build_check(check_type, check_name, check_params))

    return ChainedCheck(name, checks=inner_checks)
