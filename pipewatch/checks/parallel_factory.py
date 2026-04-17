"""Factory helper for building a ParallelCheck from a params dict."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.checks.parallel import ParallelCheck
from pipewatch.checks.factory import CheckBuildError, build_check


def build_parallel_from_params(name: str, params: Dict[str, Any]) -> ParallelCheck:
    """Build a :class:`ParallelCheck` from a *params* mapping.

    Expected params keys:
    - ``checks`` (required): list of check-config dicts, each with ``type``
      and optionally ``name`` / ``params``.
    - ``timeout`` (optional, float): per-run wall-clock timeout in seconds.
    """
    raw_checks = params.get("checks")
    if not raw_checks:
        raise CheckBuildError(
            "ParallelCheck requires a non-empty 'checks' list in params"
        )
    if not isinstance(raw_checks, list):
        raise CheckBuildError("'checks' must be a list of check config dicts")

    timeout: float = float(params.get("timeout", 30.0))
    parallel = ParallelCheck(name=name, timeout=timeout)

    for i, entry in enumerate(raw_checks):
        if not isinstance(entry, dict):
            raise CheckBuildError(
                f"Entry {i} in 'checks' must be a dict, got {type(entry).__name__}"
            )
        sub_name = entry.get("name", f"{name}_sub_{i}")
        sub_type = entry.get("type")
        if not sub_type:
            raise CheckBuildError(f"Entry {i} in 'checks' missing 'type'")
        sub_params = entry.get("params", {})
        parallel.add_check(build_check(sub_name, sub_type, sub_params))

    return parallel
