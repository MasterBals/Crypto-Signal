from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RuntimeState:
    def __init__(self, path: str = "/data/state/runtime_state.json") -> None:
        self.path = Path(path)

    def write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
