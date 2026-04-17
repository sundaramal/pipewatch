"""WeightedCheck: runs multiple sub-checks and passes only if the
weighted score of passing checks meets a minimum threshold."""

from __future__ import annotations
from typing import List, Tuple
from pipewatch.checks.base import BaseCheck, CheckResult


class WeightedCheck(BaseCheck):
    """Aggregate check that weights sub-check results.

    Parameters (via params)
    -----------------------
    min_score : float
        Minimum weighted score (0.0–1.0) required to pass.
        Defaults to 1.0 (all checks must pass).
    """

    def __init__(self, name: str, params: dict | None = None):
        super().__init__(name, params)
        self._checks: List[Tuple[BaseCheck, float]] = []
        self._min_score: float = float((params or {}).get("min_score", 1.0))
        if not 0.0 <= self._min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")

    def add_check(self, check: BaseCheck, weight: float = 1.0) -> None:
        if weight <= 0:
            raise ValueError("weight must be positive")
        self._checks.append((check, weight))

    @property
    def checks(self) -> List[Tuple[BaseCheck, float]]:
        return list(self._checks)

    def run(self) -> CheckResult:
        if not self._checks:
            return CheckResult(name=self.name, passed=True, message="No sub-checks defined")

        total_weight = sum(w for _, w in self._checks)
        passed_weight = 0.0
        messages = []

        for check, weight in self._checks:
            result = check.run()
            if result.passed:
                passed_weight += weight
            messages.append(f"{'PASS' if result.passed else 'FAIL'} [{weight}] {check.name}: {result.message}")

        score = passed_weight / total_weight
        passed = score >= self._min_score
        summary = f"Score {score:.2f} ({'>=': '>='} min {self._min_score:.2f})"
        return CheckResult(
            name=self.name,
            passed=passed,
            message=f"{summary} | " + " | ".join(messages),
        )
