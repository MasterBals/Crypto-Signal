from __future__ import annotations

from pathlib import Path


def is_duplicate(path: Path) -> bool:
    return path.exists()
