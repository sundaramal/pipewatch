"""CLI sub-command: `pipewatch history` — display recent run history."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pipewatch.history import DEFAULT_HISTORY_PATH, HistoryStore


def _status_symbol(passed: bool) -> str:
    return "\u2705" if passed else "\u274c"


def print_history(
    pipeline: Optional[str] = None,
    limit: int = 20,
    history_path: Path = DEFAULT_HISTORY_PATH,
) -> int:
    """Print run history to stdout.  Returns exit code."""
    store = HistoryStore(path=history_path)
    entries = store.load(pipeline=pipeline, limit=limit)

    if not entries:
        label = f" for pipeline '{pipeline}'" if pipeline else ""
        print(f"No history found{label}.")
        return 0

    header = f"{'Timestamp':<32} {'Pipeline':<20} {'Pass':>5} {'Fail':>5} {'Total':>6}  Status"
    print(header)
    print("-" * len(header))
    for e in entries:
        print(
            f"{e.timestamp:<32} {e.pipeline:<20} {e.num_passed:>5} {e.num_failed:>5}"
            f" {e.total:>6}  {_status_symbol(e.passed)}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch history",
        description="Show recent pipeline run history.",
    )
    parser.add_argument(
        "--pipeline",
        metavar="NAME",
        default=None,
        help="Filter by pipeline name.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Maximum number of entries to display (default: 20).",
    )
    parser.add_argument(
        "--history-file",
        default=str(DEFAULT_HISTORY_PATH),
        metavar="PATH",
        help="Path to the history JSONL file.",
    )
    return parser


def main(argv: Optional[list] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = print_history(
        pipeline=args.pipeline,
        limit=args.limit,
        history_path=Path(args.history_file),
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
