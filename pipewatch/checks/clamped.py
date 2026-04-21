"""ClampedCheck — wraps a check and clamps its numeric result to [min_val, max_val].

If the wrapped check returns a numeric message value, the clamped value is
used when evaluating the result.  Non-numeric messages pass through unchanged.
"""
from __future__ import annotations

from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ClampedCheck(BaseCheck):
    """Clamp the numeric result of a wrapped check to a given range.

    Parameters
    ----------
    wrapped:  The inner check whose result will be clamped.
    min_val:  Lower bound (inclusive).  ``None`` means no lower bound.
    max_val:  Upper bound (inclusive).  ``None`` means no upper bound.
    name:     Optional display name.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        if min_val is not None and max_val is not None and min_val > max_val:
            raise ValueError(
                f"min_val ({min_val}) must be <= max_val ({max_val})"
            )
        super().__init__(name=name or f"clamped({wrapped.name})")
        self._wrapped = wrapped
        self._min_val = min_val
        self._max_val = max_val

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def min_val(self) -> Optional[float]:
        return self._min_val

    @property
    def max_val(self) -> Optional[float]:
        return self._max_val

    def run(self) -> CheckResult:
        result = self._wrapped.run()

        try:
            value = float(result.message)
        except (TypeError, ValueError):
            # Non-numeric message — return as-is.
            return result

        clamped = value
        if self._min_val is not None:
            clamped = max(clamped, self._min_val)
        if self._max_val is not None:
            clamped = min(clamped, self._max_val)

        clamped_msg = str(int(clamped) if clamped == int(clamped) else clamped)
        return CheckResult(passed=result.passed, message=clamped_msg)
