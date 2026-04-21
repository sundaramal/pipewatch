"""PinnedCheck — fails if the wrapped check's result changes from a previously pinned value."""
from __future__ import annotations

from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class PinnedCheck(BaseCheck):
    """Wrap a check and fail whenever its pass/fail outcome differs from the pinned baseline.

    The first call always succeeds and pins the baseline result.  Every
    subsequent call compares the wrapped result against that baseline and
    fails (with a descriptive message) when the outcome has flipped.

    Args:
        check: The inner :class:`BaseCheck` to delegate to.
        name:  Optional display name; defaults to ``"pinned(<inner.name>)"``.
    """

    def __init__(self, check: BaseCheck, *, name: Optional[str] = None) -> None:
        super().__init__(name=name or f"pinned({check.name})")
        self._wrapped = check
        self._pinned: Optional[bool] = None  # None means not yet pinned

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def pinned_value(self) -> Optional[bool]:
        """The pinned pass/fail baseline, or *None* if not yet established."""
        return self._pinned

    def reset(self) -> None:
        """Clear the pinned baseline so the next run re-pins."""
        self._pinned = None

    def run(self) -> CheckResult:
        result = self._wrapped.run()

        if self._pinned is None:
            # First run — pin the baseline and report success.
            self._pinned = result.passed
            return CheckResult(
                name=self.name,
                passed=True,
                message=f"Pinned baseline as {'PASS' if result.passed else 'FAIL'}: {result.message}",
            )

        if result.passed == self._pinned:
            return CheckResult(
                name=self.name,
                passed=True,
                message=f"Result unchanged (pinned={'PASS' if self._pinned else 'FAIL'}): {result.message}",
            )

        # Outcome has drifted from the pinned baseline.
        expected = "PASS" if self._pinned else "FAIL"
        actual = "PASS" if result.passed else "FAIL"
        return CheckResult(
            name=self.name,
            passed=False,
            message=(
                f"Pinned value drift detected: expected {expected}, got {actual}. "
                f"Inner message: {result.message}"
            ),
        )
