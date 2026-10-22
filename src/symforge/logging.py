from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable


@dataclass
class ResultLogger:
    """JSONL results logger with deterministic ordering for keys."""

    path: str

    def __post_init__(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._fh = open(self.path, "a", encoding="utf-8")

    def log(self, record: Dict[str, Any]) -> None:
        record = dict(record)
        record.setdefault("ts", time.time())
        self._fh.write(json.dumps(record, sort_keys=True) + "\n")
        self._fh.flush()

    def log_many(self, records: Iterable[Dict[str, Any]]) -> None:
        for record in records:
            self.log(record)

    def close(self) -> None:
        self._fh.close()


def results_path(name: str, results_dir: str = "results") -> str:
    if not name.endswith(".jsonl"):
        name = f"{name}.jsonl"
    return os.path.join(results_dir, name)
