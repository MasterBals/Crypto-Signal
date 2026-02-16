from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import ta


@dataclass
class AnalysisOutput:
    features: dict
    signal: dict


class MultiTimeframeAnalyzer:
    def __init__(self, min_rr: float = 2.2) -> None:
        self.min_rr = min_rr

    @staticmethod
    def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        frame = df.copy()
        frame["ema20"] = ta.trend.ema_indicator(frame["close"], window=20)
        frame["ema50"] = ta.trend.ema_indicator(frame["close"], window=50)
        frame["ema200"] = ta.trend.ema_indicator(frame["close"], window=200)
        frame["rsi14"] = ta.momentum.rsi(frame["close"], window=14)
        frame["atr14"] = ta.volatility.average_true_range(frame["high"], frame["low"], frame["close"], window=14)
        frame["vwap"] = ta.volume.volume_weighted_average_price(frame["high"], frame["low"], frame["close"], frame["volume"])
        frame["volume_delta"] = frame["volume"].diff().fillna(0)
        frame["swing_high"] = frame["high"].rolling(5).max()
        frame["swing_low"] = frame["low"].rolling(5).min()
        frame["bos_bull"] = (frame["close"] > frame["swing_high"].shift(1)).astype(int)
        frame["bos_bear"] = (frame["close"] < frame["swing_low"].shift(1)).astype(int)
        frame["fvg"] = ((frame["low"].shift(-1) > frame["high"]) | (frame["high"].shift(-1) < frame["low"])).astype(int)
        frame["orderblock"] = ((frame["volume"] > frame["volume"].rolling(20).mean()) & (frame["close"] < frame["open"])).astype(int)
        frame["liquidity_sweep"] = (frame["low"] < frame["swing_low"].shift(1)).astype(int)
        return frame

    def build_features(self, h4: pd.DataFrame, h1: pd.DataFrame, m15: pd.DataFrame, session_score: float) -> dict:
        h4i = self._add_indicators(h4).iloc[-1]
        h1i = self._add_indicators(h1).iloc[-1]
        m15df = self._add_indicators(m15)
        m15i = m15df.iloc[-1]
        atr_avg = m15df["atr14"].tail(50).mean()
        atr_expansion = float(m15i["atr14"] / atr_avg) if atr_avg else 0.0

        return {
            "ema_distance_ratio": float((m15i["ema20"] - m15i["ema50"]) / max(m15i["close"], 1e-6)),
            "rsi_slope": float(m15df["rsi14"].diff().tail(5).mean()),
            "atr_expansion_ratio": atr_expansion,
            "distance_to_vwap": float((m15i["close"] - m15i["vwap"]) / max(m15i["close"], 1e-6)),
            "session_score": session_score,
            "volatility_spike_score": float(np.clip(atr_expansion, 0, 3) / 3),
            "structure_strength_index": float((m15i["bos_bull"] + m15i["orderblock"] + m15i["fvg"]) / 3),
            "liquidity_grab_score": float(m15i["liquidity_sweep"]),
            "h4_trend_bull": int(h4i["ema50"] > h4i["ema200"]),
            "h1_trend_bull": int(h1i["ema50"] > h1i["ema200"]),
            "m15_bos_bull": int(m15i["bos_bull"]),
            "atr14": float(m15i["atr14"]),
        }

    def evaluate_signal(self, features: dict, ai_probability: float, close_price: float) -> dict:
        long_ok = (
            features["h4_trend_bull"] == 1
            and features["m15_bos_bull"] == 1
            and features["liquidity_grab_score"] > 0
            and features["atr_expansion_ratio"] > 1.2
        )
        short_ok = not long_ok
        technical_confluence = min(
            1.0,
            0.2 * features["h4_trend_bull"]
            + 0.2 * features["m15_bos_bull"]
            + 0.2 * features["liquidity_grab_score"]
            + 0.2 * (1 if features["atr_expansion_ratio"] > 1.2 else 0)
            + 0.2 * features["structure_strength_index"],
        )
        confidence = technical_confluence * 0.6 + ai_probability * 0.4
        stop_distance = 1.2 * max(features["atr14"], 1e-6)
        take_profit = close_price + (stop_distance * self.min_rr)
        return {
            "direction": "LONG" if long_ok else "SHORT" if short_ok else "NONE",
            "valid": ai_probability > 0.72 and confidence > 0.7,
            "technical_confluence": technical_confluence,
            "confidence_score": confidence,
            "ai_probability": ai_probability,
            "risk_reward": self.min_rr,
            "entry": close_price,
            "stop": close_price - stop_distance,
            "take_profit": take_profit,
        }
