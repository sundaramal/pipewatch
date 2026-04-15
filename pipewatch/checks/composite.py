"""Composite check that aggregates multiple sub-checks into one."""
from __future__ import annotations

from typing import List

from pipewatch.checks.base import BaseCheck, CheckResult


class CompositeCheck(BaseCheck):
    """Runs a collection of sub-checks and reports an aggregate result.

    The composite check passes only when *all* sub-checks pass.
    The detail message lists every sub-check result.
    """

    def __init__(self, name: str, checks: List[BaseCheck]) -> None:
        super().__init__(name)
        if not checks:
            raise ValueError("CompositeCheck requires at least one sub-check.")
        self._checks = checks

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        results: List[CheckResult] = [c.run() for c in self._checks]
        failed = [r for r in results if not r.passed]
        overall_passed = len(failed) == 0

        lines = [f"  [{'+' if r.passed else 'x'}] {r.name}: {r.detail}" for r in results]
        detail = "All sub-checks passed." if overall_passed else (
            f"{len(failed)} of {len(results)} sub-check(s) failed:\n" + "\n".join(lines)
        )

        return CheckResult(
            name=self.name,
            passed=overall_passed,
            detail=detail,
        )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def checks(self) -> List[BaseCheck]:
        """Read-only view of the sub-checks."""
        return list(self._checks)
