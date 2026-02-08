from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass
class TradeCounter:
    state_path: Path = Path("/data/state/trade_counter.json")
    timezone: str = "Europe/Zurich"

    def _today(self) -> date:
        return datetime.now(ZoneInfo(self.timezone)).date()

    def _load(self) -> dict:
        if not self.state_path.exists():
            return {"date": self._today().isoformat(), "count": 0}
        with self.state_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self, payload: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def ensure_today(self) -> dict:
        payload = self._load()
        today = self._today().isoformat()
        if payload.get("date") != today:
            payload = {"date": today, "count": 0}
            self._save(payload)
        return payload

    def increment(self) -> dict:
        payload = self.ensure_today()
        payload["count"] = int(payload.get("count", 0)) + 1
        self._save(payload)
        return payload
