from __future__ import annotations

from typing import Any


def compute_indicators(market_data: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """Placeholder indicator computation."""
    return {
        "rsi": float(config["analysis"]["rsi_period"]),
        "atr": float(config["analysis"]["atr_period"]),
    }
