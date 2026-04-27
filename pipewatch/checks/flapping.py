"""FlappingCheck — skips or flags a check that alternates pass/fail too rapidly.

A check is considered "flapping" when it has changed state more than
`threshold` times within the last `window` consecutive runs.  While
flapping the wrapper returns a skipped (passing) result so that noisy
checks don't spam alerts, and it records the flap count in the message.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class FlappingCheck(BaseCheck):
    """Wraps *wrapped* and suppresses results while the check is flapping.

    Parameters
    ----------
    wrapped:
        The inner :class:`BaseCheck` to delegate to.
    threshold:
        Number of state-changes within *window* runs that triggers the
        flapping state.  Defaults to ``3``.
    window:
        How many recent run outcomes to consider.  Defaults to ``5``.
    name:
        Optional display name; falls back to the wrapped check's name.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        threshold: int = 3,
        window: int = 5,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._threshold = threshold
        self._window = window
        # Store booleans: True == passed, False == failed
        self._history: deque[bool] = deque(maxlen=window)

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def window(self) -> int:
        return self._window

    def _flap_count(self) -> int:
        """Return the number of state transitions in the current history."""
        transitions = 0
        history = list(self._history)
        for i in range(1, len(history)):
            if history[i] != history[i - 1]:
                transitions += 1
        return transitions

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        self._history.append(result.passed)

        flaps = self._flap_count()
        if len(self._history) >= 2 and flaps >= self._threshold:
            return CheckResult(
                passed=True,
                name=self.name,
                message=(
                    f"[flapping] suppressed — {flaps} state-changes in last "
                    f"{len(self._history)} runs"
                ),
            )
        return CheckResult(passed=result.passed, name=self.name, message=result.message)
