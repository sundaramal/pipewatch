"""EveryCheck — passes only if all sub-checks pass (strict AND, with short-circuit)."""
from __future__ import annotations

from typing import List

from pipewatch.checks.base import BaseCheck, CheckResult


class EveryCheck(BaseCheck):
    """Runs all sub-checks and passes only when every one passes.

    Unlike CompositeCheck (which aggregates), EveryCheck short-circuits on the
    first failure and surfaces that failure message directly.
    """

    def __init__(self, name: str = "every") -> None:
        super().__init__(name=name)
        self._checks: List[BaseCheck] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_check(self, check: BaseCheck) -> "EveryCheck":
        """Append *check* and return *self* for chaining."""
        self._checks.append(check)
        return self

    @property
    def checks(self) -> List[BaseCheck]:
        return list(self._checks)

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        if not self._checks:
            return CheckResult(
                name=self.name,
                passed=True,
                message="no sub-checks defined",
            )

        for check in self._checks:
            result = check.run()
            if not result.passed:
                return CheckResult(
                    name=self.name,
                    passed=False,
                    message=f"[{check.name}] {result.message}",
                )

        return CheckResult(
            name=self.name,
            passed=True,
            message=f"all {len(self._checks)} sub-check(s) passed",
        )
