"""Factory helper for building EveryCheck instances from parameter dicts.

This module provides ``build_every_from_params``, which is called by the
generic check factory when the check type is ``"every"``.

Expected params shape
---------------------
.. code-block:: python

    {
        "checks": [
            {"type": "threshold", "name": "row_count", ...},
            {"type": "freshness",  "name": "last_run",  ...},
        ]
    }

All entries in ``checks`` are resolved through the same
:func:`pipewatch.checks.factory.build_check` pipeline so that nested
wrapper types (retry, timeout, …) are supported transparently.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pipewatch.checks.every import EveryCheck


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def build_every_from_params(params: Dict[str, Any]) -> EveryCheck:
    """Build an :class:`~pipewatch.checks.every.EveryCheck` from *params*.

    Parameters
    ----------
    params:
        Arbitrary keyword parameters extracted from the YAML/JSON config
        block for this check.  Must contain a ``"checks"`` key whose value
        is a non-empty list of check-config dicts.

    Returns
    -------
    EveryCheck
        A fully initialised instance whose sub-checks are built recursively.

    Raises
    ------
    ValueError
        If ``"checks"`` is missing, empty, or contains a non-dict entry.
    """
    # Avoid circular import — factory imports registry which imports this.
    from pipewatch.checks.factory import build_check  # noqa: PLC0415

    raw_checks: List[Dict[str, Any]] = params.get("checks", [])

    if not raw_checks:
        raise ValueError(
            "build_every_from_params: 'checks' key is required and must be "
            "a non-empty list."
        )

    every = EveryCheck(name=params.get("name", "every"))

    for idx, entry in enumerate(raw_checks):
        if not isinstance(entry, dict):
            raise ValueError(
                f"build_every_from_params: entry at index {idx} must be a "
                f"dict, got {type(entry).__name__!r}."
            )
        sub_check = build_check(entry)
        every.add_check(sub_check)

    return every
