"""GroupedCheck: run sub-checks organised by a string key and report per-group.

This wrapper is useful when you want to partition a set of checks into named
buckets (e.g. by data source, by team, or by severity) and surface per-group
pass/fail summaries alongside the individual results.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class GroupedCheck(BaseCheck):
    """Run multiple sub-checks organised into named groups.

    Each sub-check is assigned to exactly one group label.  When ``run()`` is
    called every sub-check is executed and the overall result is *passed* only
    when **all** sub-checks pass.  The ``message`` on the returned
    :class:`~pipewatch.checks.base.CheckResult` contains a compact per-group
    summary so that failures are easy to triage at a glance.

    Example usage::

        gc = GroupedCheck(name="pipeline_health")
        gc.add_check("ingestion", ThresholdCheck("row_count", value=500, min_val=1))
        gc.add_check("ingestion", FreshnessCheck("last_run", max_age_seconds=3600))
        gc.add_check("transform", ThresholdCheck("error_rate", value=0.01, max_val=0.05))
        result = gc.run()
    """

    def __init__(self, name: str = "grouped") -> None:
        super().__init__(name=name)
        # Ordered mapping of group_label -> list of checks
        self._groups: Dict[str, List[BaseCheck]] = defaultdict(list)
        # Preserve insertion order of group labels for deterministic output
        self._group_order: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_check(self, group: str, check: BaseCheck) -> "GroupedCheck":
        """Add *check* to *group*, creating the group if it does not exist.

        Returns ``self`` so calls can be chained.
        """
        if not isinstance(check, BaseCheck):
            raise TypeError(
                f"Expected a BaseCheck instance, got {type(check).__name__!r}"
            )
        if group not in self._groups:
            self._group_order.append(group)
        self._groups[group].append(check)
        return self

    @property
    def groups(self) -> Dict[str, List[BaseCheck]]:
        """Read-only view of the current group → checks mapping."""
        return {g: list(checks) for g, checks in self._groups.items()}

    @property
    def group_names(self) -> List[str]:
        """Ordered list of group labels."""
        return list(self._group_order)

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        """Execute every sub-check and return an aggregated :class:`CheckResult`.

        The overall check passes only when every sub-check in every group
        passes.  The result message contains a per-group breakdown listing
        how many checks passed and failed within each group.
        """
        if not self._groups:
            return CheckResult(
                name=self.name,
                passed=True,
                message="no checks registered",
            )

        group_summaries: List[str] = []
        overall_passed = True

        for group_label in self._group_order:
            checks = self._groups[group_label]
            results = [c.run() for c in checks]
            num_pass = sum(1 for r in results if r.passed)
            num_fail = len(results) - num_pass

            if num_fail > 0:
                overall_passed = False
                group_summaries.append(
                    f"{group_label}: {num_fail} failed / {len(results)} total"
                )
            else:
                group_summaries.append(
                    f"{group_label}: all {len(results)} passed"
                )

        message = "; ".join(group_summaries)
        return CheckResult(name=self.name, passed=overall_passed, message=message)
