"""SampledCheck — runs the wrapped check only a fraction of the time."""
from __future__ import annotations

import random
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class SampledCheck(BaseCheck):
    """Wraps a check and runs it with a given probability (0.0–1.0).

    When the check is skipped due to sampling, a passing result is returned
    with a note indicating it was not evaluated.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        rate: float = 1.0,
        name: Optional[str] = None,
        *,
        _rng: Optional[random.Random] = None,
    ) -> None:
        if not (0.0 <= rate <= 1.0):
            raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")
        super().__init__(name=name or f"sampled({wrapped.name})")
        self._wrapped = wrapped
        self._rate = rate
        self._rng = _rng or random.Random()

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def rate(self) -> float:
        return self._rate

    def run(self) -> CheckResult:
        if self._rng.random() > self._rate:
            return CheckResult(
                passed=True,
                message=f"[sampled] skipped '{self._wrapped.name}' (rate={self._rate})",
            )
        result = self._wrapped.run()
        return CheckResult(
            passed=result.passed,
            message=f"[sampled] {result.message}",
        )
