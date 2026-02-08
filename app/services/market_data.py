from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


def get_candles() -> pd.DataFrame:
    """
    Holt Candles via yfinance.
    Erwartet Spalten: Open, High, Low, Close, Volume (Volume kann bei FX leer sein).
    Index ist DatetimeIndex.
    """
    period = f"{settings.history_days}d"
    df = yf.download(
        tickers=settings.pair_symbol_yf,
        period=period,
        interval=settings.candle_interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if df is None or df.empty:
        raise RuntimeError("Keine Marktdaten von yfinance erhalten.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.rename(columns={c: c.title() for c in df.columns})
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            raise RuntimeError(f"Unerwartetes Datenformat: Spalte '{col}' fehlt.")
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    return df


def get_price_from_candles(df: pd.DataFrame) -> float:
    return float(df["Close"].iloc[-1])


def get_tradingview_summary() -> dict[str, Any] | None:
    """
    TradingView TA liefert Indikatoren- und Summary-Signale (inoffiziell/indirekt),
    daher nur als Zusatzinfo, nicht als harte Abhaengigkeit.
    """
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
