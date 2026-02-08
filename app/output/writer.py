from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.output.deduplicator import is_duplicate


@dataclass
class SignalWriter:
    base_path: Path = Path("/data/signals")

    def build_path(self, symbol: str, interval: str, timestamp: datetime) -> Path:
        year = f"{timestamp.year:04d}"
        month = f"{timestamp.month:02d}"
        day = f"{timestamp.day:02d}"
        filename = f"{symbol}_{interval}_{timestamp.strftime('%H%M')}.json"
        return self.base_path / year / month / day / filename

    def write(self, payload: dict[str, Any], symbol: str, interval: str, timestamp: datetime) -> Path:
        path = self.build_path(symbol, interval, timestamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        if is_duplicate(path):
            return path
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return path
