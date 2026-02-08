from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    out = 100 - (100 / (1 + rs))
    return out.fillna(50.0)


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def compute_indicators(df: pd.DataFrame) -> dict[str, float]:
    close = df["Close"]
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    rsi14 = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    atr14 = atr(df, 14)

    return {
        "ema20": float(ema20.iloc[-1]),
        "ema50": float(ema50.iloc[-1]),
        "rsi14": float(rsi14.iloc[-1]),
        "macd": float(macd_line.iloc[-1]),
        "macd_signal": float(signal_line.iloc[-1]),
        "macd_hist": float(hist.iloc[-1]),
        "atr14": float(atr14.iloc[-1]),
    }


def technical_score(df: pd.DataFrame) -> tuple[float, dict[str, float]]:
    """
    Score in [-1..+1].
    Logik:
    - Trend: EMA20 vs EMA50
    - Momentum: MACD Histogramm
    - Mean Reversion/Overbought/Oversold: RSI
    """
    ind = compute_indicators(df)
    score = 0.0

    if ind["ema20"] > ind["ema50"]:
        score += 0.35
    elif ind["ema20"] < ind["ema50"]:
        score -= 0.35

    if ind["macd_hist"] > 0:
        score += 0.25
    elif ind["macd_hist"] < 0:
        score -= 0.25

    r = ind["rsi14"]
    if r < 30:
        score += 0.30
    elif r > 70:
        score -= 0.30
    else:
        score += 0.10 if ind["ema20"] > ind["ema50"] else (-0.10 if ind["ema20"] < ind["ema50"] else 0.0)

    score = max(-1.0, min(1.0, score))
    return score, ind
