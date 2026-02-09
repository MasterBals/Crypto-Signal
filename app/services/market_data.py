from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests

import pandas as pd
import yfinance as yf

try:
    from tradingview_ta import TA_Handler, Interval
except Exception:
    TA_Handler = None
    Interval = None

from app.config import get_instrument, settings
from app.services.db import load_candles, upsert_candles


@dataclass
class MarketSnapshot:
    price: float
    candles: pd.DataFrame
    tv_summary: dict[str, Any] | None


def _download(symbol: str) -> pd.DataFrame:
    period = f"{settings.history_days}d"
    df = yf.download(
        tickers=symbol,
        period=period,
        interval=settings.candle_interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"Keine Marktdaten fuer {symbol} erhalten.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.rename(columns={c: c.title() for c in df.columns})
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            raise RuntimeError(f"Unerwartetes Datenformat: Spalte '{col}' fehlt.")
    return df.dropna(subset=["Open", "High", "Low", "Close"]).copy()


def _granularity_seconds() -> int:
    interval = settings.candle_interval
    allowed = [60, 300, 900, 3600, 21600, 86400]
    if interval.endswith("m"):
        minutes = int(interval.replace("m", ""))
        target = minutes * 60
    elif interval.endswith("h"):
        hours = int(interval.replace("h", ""))
        target = hours * 3600
    else:
        target = 900
    return min(allowed, key=lambda x: abs(x - target))


def _alphavantage_interval() -> str:
    interval = settings.candle_interval
    allowed = [1, 5, 15, 30, 60]
    if interval.endswith("m"):
        minutes = int(interval.replace("m", ""))
    elif interval.endswith("h"):
        minutes = int(interval.replace("h", "")) * 60
    else:
        minutes = 15
    closest = min(allowed, key=lambda x: abs(x - minutes))
    return f"{closest}min"


def _download_alphavantage_fx(api_key: str, from_symbol: str, to_symbol: str) -> pd.DataFrame:
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "interval": _alphavantage_interval(),
        "apikey": api_key,
        "outputsize": "full",
    }
    response = requests.get("https://www.alphavantage.co/query", params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("AlphaVantage liefert ein unerwartetes Antwortformat.")
    if "Error Message" in payload or "Information" in payload:
        raise RuntimeError(payload.get("Error Message") or payload.get("Information") or "AlphaVantage-Fehler.")
    series_key = next((key for key in payload.keys() if key.startswith("Time Series FX")), None)
    if not series_key:
        raise RuntimeError("AlphaVantage liefert keine Zeitreihe.")
    series = payload.get(series_key, {})
    if not series:
        raise RuntimeError("AlphaVantage liefert keine Kerzendaten.")
    df = pd.DataFrame.from_dict(series, orient="index")
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.rename(
        columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
        }
    )
    df = df[["Open", "High", "Low", "Close"]].astype(float)
    return df.sort_index()


def _download_coinbase(product_id: str) -> pd.DataFrame:
    granularity = _granularity_seconds()
    end = pd.Timestamp.utcnow()
    start = end - pd.Timedelta(days=settings.history_days)
    url = f"https://api.exchange.coinbase.com/products/{product_id}/candles"
    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "granularity": granularity,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise RuntimeError(f"Keine Coinbase-Daten fuer {product_id} erhalten.")
    df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.sort_values("time").set_index("time")
    return df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )


def _convert_to_usd(base_df: pd.DataFrame, fx_df: pd.DataFrame) -> pd.DataFrame:
    joined = base_df.join(fx_df[["Close"]].rename(columns={"Close": "fx"}), how="inner")
    if joined.empty:
        raise RuntimeError("Konvertierung fehlgeschlagen: keine Ueberschneidung der Daten.")
    for col in ["Open", "High", "Low", "Close"]:
        joined[col] = joined[col] / joined["fx"]
    return joined.drop(columns=["fx"])


def get_candles() -> pd.DataFrame:
    instrument = get_instrument()
    symbol_label = instrument["symbol"]
    since_ts = int((pd.Timestamp.utcnow() - pd.Timedelta(days=settings.history_days)).timestamp())
    provider = settings.market_data_provider
    base_df: pd.DataFrame | None = None

    try:
        if provider == "alphavantage" and settings.alphavantage_api_key:
            from_symbol = instrument.get("av_from_symbol")
            to_symbol = instrument.get("av_to_symbol")
            if from_symbol and to_symbol:
                base_df = _download_alphavantage_fx(settings.alphavantage_api_key, from_symbol, to_symbol)
        if base_df is None and provider == "coinbase" and instrument.get("product_id"):
            base_df = _download_coinbase(instrument["product_id"])
        if base_df is None:
            base_df = _download(instrument["symbol"])
            conversion_symbol = instrument.get("conversion_symbol")
            if instrument["display_currency"].upper() == "USD" and conversion_symbol:
                fx_df = _download(conversion_symbol)
                base_df = _convert_to_usd(base_df, fx_df)
                symbol_label = f"{instrument['symbol']}_USD"
        upsert_candles(symbol_label, base_df)
    except Exception:
        pass

    stored = load_candles(symbol_label, since_ts)
    if stored.empty:
        raise RuntimeError("Keine lokalen Marktdaten vorhanden.")
    return stored


def get_price_from_candles(df: pd.DataFrame) -> float:
    return float(df["Close"].iloc[-1])


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
