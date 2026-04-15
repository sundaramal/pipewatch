"""Run history tracking: persist and retrieve past RunReports."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pipewatch.runner import RunReport

DEFAULT_HISTORY_PATH = Path(os.environ.get("PIPEWATCH_HISTORY", ".pipewatch_history.jsonl"))


@dataclass
class HistoryEntry:
    timestamp: str
    pipeline: str
    total: int
    num_passed: int
    num_failed: int
    passed: bool

    @classmethod
    def from_report(cls, report: RunReport, pipeline: str) -> "HistoryEntry":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            pipeline=pipeline,
            total=report.total,
            num_passed=report.num_passed,
            num_failed=report.num_failed,
            passed=report.passed,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, line: str) -> "HistoryEntry":
        return cls(**json.loads(line))


class HistoryStore:
    """Append-only JSONL store for run history."""

    def __init__(self, path: Path = DEFAULT_HISTORY_PATH) -> None:
        self.path = Path(path)

    def record(self, report: RunReport, pipeline: str) -> HistoryEntry:
        entry = HistoryEntry.from_report(report, pipeline)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_json() + "\n")
        return entry

    def load(self, pipeline: Optional[str] = None, limit: int = 100) -> List[HistoryEntry]:
        if not self.path.exists():
            return []
        entries: List[HistoryEntry] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = HistoryEntry.from_json(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                if pipeline is None or entry.pipeline == pipeline:
                    entries.append(entry)
        return entries[-limit:]

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
