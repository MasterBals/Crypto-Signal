from __future__ import annotations

import threading
import time
from typing import Any

import pandas as pd

from app.config import settings
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

    payload = {
        "updated_epoch": int(time.time()),
        "signal": {
            "action": sig.action,
            "entry": sig.entry,
            "stop_loss": sig.stop_loss,
            "take_profit": sig.take_profit,
            "confidence": sig.confidence,
            "score": round(sig.score, 4),
            "reason": sig.reason,
        },
        "market": {
            "price": sig.details.get("price"),
        },
        "indicators": sig.details.get("technical", {}),
        "news": sig.details.get("news", []),
        "meta": {
            "pair": "EUR/JPY",
            "interval": settings.candle_interval,
            "refresh_seconds": settings.refresh_seconds,
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
        return refresh_state()
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
