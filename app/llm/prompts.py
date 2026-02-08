from __future__ import annotations

from typing import Any


def build_prompt(market_input: dict[str, Any]) -> str:
    return (
        "You are a trading assistant. Return JSON with decision, entry, stop_loss, take_profit, "
        "confidence, valid_until, reasons.\n" + f"Input: {market_input}"
    )
