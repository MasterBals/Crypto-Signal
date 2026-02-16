from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def synthetic_candles(points: int, freq_minutes: int) -> pd.DataFrame:
    base = 160.0
    idx = [datetime.utcnow() - timedelta(minutes=freq_minutes * (points - i)) for i in range(points)]
    walk = np.cumsum(np.random.normal(0, 0.05, points)) + base
    close = pd.Series(walk)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = np.maximum(open_, close) + np.random.rand(points) * 0.04
    low = np.minimum(open_, close) - np.random.rand(points) * 0.04
    volume = np.random.randint(100, 900, points)
    return pd.DataFrame({"time": idx, "open": open_, "high": high, "low": low, "close": close, "volume": volume})
