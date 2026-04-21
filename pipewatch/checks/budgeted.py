"""BudgetedCheck — wraps a check and enforces a run-count budget.

Once the budget (maximum number of allowed runs) is exhausted the check
is skipped and a passing result with a descriptive message is returned,
preventing noisy or expensive checks from running indefinitely.
"""

from __future__ import annotations

from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class BudgetedCheck(BaseCheck):
    """A decorator check that limits how many times the inner check may run.

    Parameters
    ----------
    check:
        The inner :class:`~pipewatch.checks.base.BaseCheck` to wrap.
    budget:
        Maximum number of times the inner check will actually be executed.
        Must be a positive integer.
    name:
        Optional display name.  Defaults to the inner check's name prefixed
        with ``"budgeted:"``.

    Example
    -------
    >>> inner = ThresholdCheck("row_count", value=50, min_val=0, max_val=100)
    >>> check = BudgetedCheck(inner, budget=3)
    >>> for _ in range(5):
    ...     result = check.run()
    # Runs 1-3 execute the inner check; runs 4-5 return a skip result.
    """

    def __init__(
        self,
        check: BaseCheck,
        budget: int,
        name: Optional[str] = None,
    ) -> None:
        if budget < 1:
            raise ValueError(f"budget must be >= 1, got {budget!r}")
        super().__init__(name=name or f"budgeted:{check.name}")
        self._check = check
        self._budget = budget
        self._runs: int = 0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def wrapped(self) -> BaseCheck:
        """The inner check being budgeted."""
        return self._check

    @property
    def budget(self) -> int:
        """Maximum number of executions allowed."""
        return self._budget

    @property
    def runs_used(self) -> int:
        """Number of times the inner check has actually been executed."""
        return self._runs

    @property
    def budget_exhausted(self) -> bool:
        """``True`` when no further executions will be delegated."""
        return self._runs >= self._budget

    def reset(self) -> None:
        """Reset the run counter, restoring the full budget."""
        self._runs = 0

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        """Execute the inner check if budget remains; skip otherwise.

        Returns
        -------
        CheckResult
            The inner check's result when budget is available, or a
            synthetic passing result with a skip message when exhausted.
        """
        if self.budget_exhausted:
            return CheckResult(
                name=self.name,
                passed=True,
                message=(
                    f"budget of {self._budget} run(s) exhausted — "
                    "check skipped"
                ),
            )

        self._runs += 1
        result = self._check.run()
        # Re-label the result under this check's name for clarity.
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
        )
