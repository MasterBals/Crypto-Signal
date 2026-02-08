from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math
import random

import pandas as pd
import yfinance as yf

try:
    from tradingview_ta import TA_Handler, Interval
except Exception:
    TA_Handler = None
    Interval = None

from app.config import settings


@dataclass
class MarketSnapshot:
    price: float
    candles: pd.DataFrame
    tv_summary: dict[str, Any] | None


def _make_mock_candles(price: float, periods: int) -> pd.DataFrame:
    now = pd.Timestamp.utcnow().floor("min")
    step = pd.Timedelta(settings.candle_interval)
    if step <= pd.Timedelta(0):
        step = pd.Timedelta(minutes=15)
    times = [now - step * i for i in range(periods)][::-1]
    rows = []
    last = price
    for _ in times:
        drift = random.uniform(-0.1, 0.1)
        spread = abs(random.uniform(0.02, 0.12))
        open_p = last
        close_p = max(0.01, open_p + drift)
        high = max(open_p, close_p) + spread
        low = min(open_p, close_p) - spread
        rows.append({"Open": open_p, "High": high, "Low": low, "Close": close_p})
        last = close_p
    return pd.DataFrame(rows, index=pd.DatetimeIndex(times))


def get_candles() -> pd.DataFrame:
    period = f"{settings.history_days}d"
    try:
        df = yf.download(
            tickers=settings.pair_symbol_yf,
            period=period,
            interval=settings.candle_interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception:
        df = None
    if df is None or df.empty:
        return _make_mock_candles(162.5, 200)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.rename(columns={c: c.title() for c in df.columns})
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            raise RuntimeError(f"Unerwartetes Datenformat: Spalte '{col}' fehlt.")
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    return df


def get_price_from_candles(df: pd.DataFrame) -> float:
    try:
        price = float(df["Close"].iloc[-1])
    except Exception:
        price = math.nan
    return price


def get_tradingview_summary() -> dict[str, Any] | None:
    if TA_Handler is None or Interval is None:
        return None
    try:
        handler = TA_Handler(
            symbol="EURJPY",
            screener="forex",
            exchange="FX_IDC",
            interval=Interval.INTERVAL_15_MINUTES,
        )
        analysis = handler.get_analysis()
        return {
            "recommendation": getattr(analysis, "summary", {}).get("RECOMMENDATION"),
            "summary": getattr(analysis, "summary", {}),
            "oscillators": getattr(analysis, "oscillators", {}),
            "moving_averages": getattr(analysis, "moving_averages", {}),
        }
    except Exception:
        return None


def get_market_snapshot() -> MarketSnapshot:
    candles = get_candles()
    price = get_price_from_candles(candles)
    tv = get_tradingview_summary()
    return MarketSnapshot(price=price, candles=candles, tv_summary=tv)
