"""ValidatedCheck — wraps a check and validates its result against a schema/predicate."""
from __future__ import annotations

from typing import Callable, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ValidationError(Exception):
    """Raised when a CheckResult fails schema validation."""


class ValidatedCheck(BaseCheck):
    """Decorator that validates a CheckResult using a user-supplied predicate.

    If the predicate raises or returns False the result is replaced with a
    FAIL result that describes the validation problem.

    Parameters
    ----------
    check:
        The inner check whose result will be validated.
    validator:
        A callable ``(result: CheckResult) -> bool``.  Return ``True`` to
        accept the result; return ``False`` (or raise) to reject it.
    message:
        Optional human-readable label used in the failure message when
        validation is rejected.
    name:
        Optional override for the check name.
    """

    def __init__(
        self,
        check: BaseCheck,
        validator: Callable[[CheckResult], bool],
        *,
        message: str = "result failed validation",
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"validated({check.name})")
        self._check = check
        self._validator = validator
        self._message = message

    @property
    def wrapped(self) -> BaseCheck:
        return self._check

    def run(self) -> CheckResult:
        result = self._check.run()
        try:
            accepted = self._validator(result)
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                passed=False,
                message=f"{self.name}: validator raised {type(exc).__name__}: {exc}",
            )
        if not accepted:
            return CheckResult(
                passed=False,
                message=f"{self.name}: {self._message}",
            )
        return result
