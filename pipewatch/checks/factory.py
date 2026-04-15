"""Factory for constructing check instances from config objects."""

from typing import List
from pipewatch.checks.base import BaseCheck
from pipewatch.checks.registry import get
from pipewatch.config import CheckConfig


class CheckBuildError(Exception):
    """Raised when a check cannot be constructed from config."""


def build_check(config: CheckConfig) -> BaseCheck:
    """Instantiate a single check from a CheckConfig.

    Args:
        config: A CheckConfig dataclass with name, type, and params.

    Returns:
        An instantiated BaseCheck subclass.

    Raises:
        CheckBuildError: If the type is unknown or params are invalid.
    """
    try:
        check_cls = get(config.check_type)
    except KeyError as exc:
        raise CheckBuildError(str(exc)) from exc

    try:
        return check_cls(name=config.name, **config.params)
    except (TypeError, ValueError) as exc:
        raise CheckBuildError(
            f"Failed to build check '{config.name}' "
            f"(type='{config.check_type}'): {exc}"
        ) from exc


def build_checks(configs: List[CheckConfig]) -> List[BaseCheck]:
    """Instantiate multiple checks from a list of CheckConfig objects.

    Args:
        configs: List of CheckConfig dataclass instances.

    Returns:
        List of instantiated BaseCheck subclasses.

    Raises:
        CheckBuildError: If any check cannot be constructed.
    """
    return [build_check(cfg) for cfg in configs]
