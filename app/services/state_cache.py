from __future__ import annotations

import threading
import time
from typing import Any

import pandas as pd

from app.config import get_instrument, settings
from app.services.market_data import get_candles
from app.services.signal_engine import generate_signal

_lock = threading.Lock()
_state: dict[str, Any] = {}
_last_update: float = 0.0


def _df_to_candles(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for idx, row in df.tail(800).iterrows():
        ts = int(pd.Timestamp(idx).timestamp())
        out.append(
            {
                "time": ts,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
            }
        )
    return out


def refresh_state() -> dict[str, Any]:
    global _state, _last_update

    sig = generate_signal()
    df = get_candles()

    instrument = get_instrument()
    pair_label = instrument["label"]

    payload = {
        "updated_epoch": int(time.time()),
        "signal": {
            "action": sig.action,
            "entry": sig.entry,
            "stop_loss": sig.stop_loss,
            "take_profit": sig.take_profit,
            "confidence": sig.confidence,
            "success_chance": sig.success_chance,
            "score": round(sig.score, 4),
            "reason": sig.reason,
            "expected_entry_hours": sig.details.get("expected_entry_hours"),
            "expected_tp_hours": sig.details.get("expected_tp_hours"),
        },
        "market": {
            "price": sig.details.get("price"),
        },
        "indicators": sig.details.get("technical", {}),
        "news": sig.details.get("news", []),
        "meta": {
            "pair": pair_label,
            "interval": settings.candle_interval,
            "refresh_seconds": settings.refresh_seconds,
            "display_currency": instrument["display_currency"],
        },
        "chart": {
            "candles": _df_to_candles(df),
        },
        "tradingview_ta": sig.details.get("tv"),
    }

    with _lock:
        _state = payload
        _last_update = time.time()

    return payload


def get_state() -> dict[str, Any]:
    with _lock:
        age = time.time() - _last_update
        cached = _state.copy()

    if not cached or age > settings.refresh_seconds:
        try:
            return refresh_state()
        except Exception as exc:
            if cached:
                cached["meta"]["error"] = str(exc)
                return cached
            return {
                "updated_epoch": int(time.time()),
                "signal": {
                    "action": "NEUTRAL",
                    "entry": None,
                    "stop_loss": None,
                    "take_profit": None,
                    "confidence": 0,
                    "success_chance": 0,
                    "score": 0,
                    "reason": "Keine Marktdaten verfuegbar.",
                    "expected_entry_hours": None,
                    "expected_tp_hours": None,
                },
                "market": {"price": None},
                "indicators": {},
                "news": [],
                "meta": {
                    "pair": "EUR/JPY",
                    "interval": settings.candle_interval,
                    "refresh_seconds": settings.refresh_seconds,
                    "display_currency": instrument["display_currency"],
                    "error": str(exc),
                },
                "chart": {"candles": []},
                "tradingview_ta": None,
            }
    return cached


def start_scheduler() -> None:
    def loop() -> None:
        while True:
            try:
                refresh_state()
            except Exception:
                pass
            time.sleep(settings.refresh_seconds)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
