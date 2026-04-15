"""Run a collection of checks and aggregate results."""

from dataclasses import dataclass, field
from typing import List

from pipewatch.checks.base import BaseCheck, CheckResult


@dataclass
class RunReport:
    """Aggregated result of running multiple checks."""

    results: List[tuple[BaseCheck, CheckResult]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.passed for _, result in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def num_passed(self) -> int:
        return sum(1 for _, r in self.results if r.passed)

    @property
    def num_failed(self) -> int:
        return self.total - self.num_passed

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.num_passed}/{self.total} checks passed, "
            f"{self.num_failed} failed"
        )


class CheckRunner:
    """Executes a list of checks and returns a RunReport."""

    def __init__(self, checks: List[BaseCheck]) -> None:
        self.checks = checks

    def run_all(self) -> RunReport:
        """Run every registered check and collect results."""
        report = RunReport()
        for check in self.checks:
            result = check.run()
            report.results.append((check, result))
        return report

    def add_check(self, check: BaseCheck) -> None:
        """Register an additional check."""
        self.checks.append(check)
