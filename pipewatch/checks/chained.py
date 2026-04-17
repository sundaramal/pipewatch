"""ChainedCheck: runs checks in sequence, stopping on first failure."""
from __future__ import annotations
from typing import List
from pipewatch.checks.base import BaseCheck, CheckResult


class ChainedCheck(BaseCheck):
    """Runs a sequence of checks; stops and returns the first failure.

    If all checks pass, returns the last check's result.
    """

    def __init__(self, name: str, checks: List[BaseCheck] | None = None) -> None:
        super().__init__(name)
        self._checks: List[BaseCheck] = list(checks) if checks else []

    @property
    def checks(self) -> List[BaseCheck]:
        return list(self._checks)

    def add_check(self, check: BaseCheck) -> None:
        self._checks.append(check)

    def run(self) -> CheckResult:
        if not self._checks:
            return CheckResult(passed=True, message="No checks in chain")
        last: CheckResult | None = None
        for check in self._checks:
            last = check.run()
            if not last.passed:
                return CheckResult(
                    passed=False,
                    message=f"Chain stopped at '{check.name}': {last.message}",
                )
        return CheckResult(passed=True, message=last.message if last else "")
