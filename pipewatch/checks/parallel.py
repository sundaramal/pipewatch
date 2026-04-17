"""ParallelCheck — run multiple checks concurrently and aggregate results."""
from __future__ import annotations

import concurrent.futures
from typing import List, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ParallelCheck(BaseCheck):
    """Run a collection of checks in parallel threads and aggregate.

    The overall check passes only when every sub-check passes.
    Individual results are surfaced in the message.
    """

    def __init__(
        self,
        name: str,
        checks: Optional[List[BaseCheck]] = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(name)
        self._checks: List[BaseCheck] = list(checks or [])
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def add_check(self, check: BaseCheck) -> None:
        self._checks.append(check)

    @property
    def checks(self) -> List[BaseCheck]:
        return list(self._checks)

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        if not self._checks:
            return CheckResult(passed=True, message="no sub-checks defined")

        results: List[CheckResult] = [None] * len(self._checks)  # type: ignore[list-item]

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self._checks)
        ) as executor:
            future_to_idx = {
                executor.submit(c.run): i for i, c in enumerate(self._checks)
            }
            done, _ = concurrent.futures.wait(
                future_to_idx, timeout=self._timeout
            )
            for future in future_to_idx:
                idx = future_to_idx[future]
                if future in done:
                    try:
                        results[idx] = future.result()
                    except Exception as exc:  # noqa: BLE001
                        results[idx] = CheckResult(
                            passed=False, message=f"exception: {exc}"
                        )
                else:
                    results[idx] = CheckResult(
                        passed=False, message="timed out"
                    )

        all_passed = all(r.passed for r in results)
        parts = [
            f"{self._checks[i].name}: {'OK' if r.passed else 'FAIL — ' + r.message}"
            for i, r in enumerate(results)
        ]
        return CheckResult(passed=all_passed, message="; ".join(parts))
