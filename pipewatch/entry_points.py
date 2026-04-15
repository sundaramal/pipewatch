"""Entry-point helpers so pipewatch can be invoked as `pipewatch <config>`.

This module exists to keep setup.cfg / pyproject.toml wiring minimal:
  [options.entry_points]
  console_scripts =
      pipewatch = pipewatch.entry_points:cli
"""

from pipewatch.cli import main as cli  # re-export for entry-point

__all__ = ["cli"]
