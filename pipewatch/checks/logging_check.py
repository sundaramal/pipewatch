"""LoggingCheck — wraps another check and logs each run result."""
from __future__ import annotations

import logging
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult

logger = logging.getLogger(__name__)


class LoggingCheck(BaseCheck):
    """Decorator check that logs the result of the wrapped check."""

    def __init__(
        self,
        check: BaseCheck,
        level: str = "INFO",
        name: Optional[str] = None,
    ) -> None:
        label = name or getattr(check, "name", check.__class__.__name__)
        super().__init__(name=label)
        self._wrapped = check
        self._level = level.upper()
        self._log_fn = getattr(logger, self._level.lower(), logger.info)

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        if result.passed:
            self._log_fn("[%s] PASS — %s", self.name, result.message)
        else:
            logger.warning("[%s] FAIL — %s", self.name, result.message)
        return result
