"""Base class and registry for pluggable pipeline check definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CheckResult:
    """Result returned by a check execution."""

    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = field(default=None)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


class BaseCheck(ABC):
    """Abstract base class for all pipeline checks."""

    #: Human-readable name for this check type.
    name: str = "base_check"

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute the check and return a CheckResult."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config!r})"


# ---------------------------------------------------------------------------
# Simple plugin registry
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, type] = {}


def register_check(cls: type) -> type:
    """Class decorator that registers a BaseCheck subclass by its *name*."""
    if not issubclass(cls, BaseCheck):
        raise TypeError(f"{cls} must subclass BaseCheck")
    _REGISTRY[cls.name] = cls
    return cls


def get_check_class(name: str) -> type:
    """Look up a registered check class by name.

    Raises:
        KeyError: if no check with *name* is registered.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(
            f"Unknown check type '{name}'. Available checks: {available}"
        ) from None


def list_checks() -> Dict[str, type]:
    """Return a copy of the current check registry."""
    return dict(_REGISTRY)
