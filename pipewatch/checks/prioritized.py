"""PrioritizedCheck — runs sub-checks in priority order and stops on the first failure.

This wrapper is useful when checks have a natural importance ordering:
high-priority checks (e.g. connectivity) should gate lower-priority ones
(e.g. data quality) so that noise from downstream failures is suppressed.
"""

from __future__ import annotations

import heapq
from typing import List, Optional, Tuple

from pipewatch.checks.base import BaseCheck, CheckResult


class PrioritizedCheck(BaseCheck):
    """Runs wrapped checks in ascending priority order (lower number = higher priority).

    Execution halts at the first failing check and returns that result.
    If all checks pass, the result of the lowest-priority (last) check is returned.

    Parameters
    ----------
    name:
        Human-readable name for this composite check.
    stop_on_first_failure:
        When *True* (default), execution stops as soon as a check fails.
        When *False*, all checks are run and the first failure encountered
        (by priority) is returned — useful for collecting full diagnostics.
    """

    def __init__(
        self,
        name: str = "prioritized",
        stop_on_first_failure: bool = True,
    ) -> None:
        super().__init__(name=name)
        self._stop_on_first_failure = stop_on_first_failure
        # heap entries: (priority, insertion_index, check)
        self._heap: List[Tuple[int, int, BaseCheck]] = []
        self._counter: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add_check(self, check: BaseCheck, priority: int = 0) -> "PrioritizedCheck":
        """Register *check* with the given *priority* (lower runs first).

        The insertion index is used as a tie-breaker so that checks added
        earlier run first among those sharing the same priority.

        Returns *self* to allow fluent chaining.
        """
        heapq.heappush(self._heap, (priority, self._counter, check))
        self._counter += 1
        return self

    @property
    def checks(self) -> List[BaseCheck]:
        """Return checks in priority order (does not mutate the heap)."""
        return [entry[2] for entry in sorted(self._heap)]

    # ------------------------------------------------------------------
    # BaseCheck implementation
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        """Execute checks in priority order.

        Behaviour depends on *stop_on_first_failure*:
        - True  → return immediately on the first failing result.
        - False → run all checks; return the highest-priority failure found,
                  or the last passing result if none failed.
        """
        if not self._heap:
            return CheckResult(
                name=self.name,
                passed=True,
                message="no checks registered",
            )

        first_failure: Optional[CheckResult] = None
        last_result: Optional[CheckResult] = None

        for _priority, _idx, check in sorted(self._heap):
            result = check.run()
            last_result = result

            if not result.passed:
                if self._stop_on_first_failure:
                    # Wrap the inner result under this check's name.
                    return CheckResult(
                        name=self.name,
                        passed=False,
                        message=(
                            f"[priority={_priority}] {check.name}: {result.message}"
                        ),
                    )
                if first_failure is None:
                    first_failure = CheckResult(
                        name=self.name,
                        passed=False,
                        message=(
                            f"[priority={_priority}] {check.name}: {result.message}"
                        ),
                    )

        if first_failure is not None:
            return first_failure

        # All checks passed — surface the last result under our name.
        return CheckResult(
            name=self.name,
            passed=True,
            message=last_result.message if last_result else "all checks passed",
        )
