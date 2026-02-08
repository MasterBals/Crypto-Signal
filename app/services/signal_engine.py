from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math

from app.config import get_instrument, settings
from app.services.market_data import get_market_snapshot
from app.services.technical_analysis import technical_score
from app.services.news_service import get_news_sentiment


@dataclass
class Signal:
    action: str
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    confidence: float
    success_chance: float
    score: float
    reason: str
    details: dict[str, Any]


def _round_fx(x: float) -> float:
    instrument = get_instrument()
    return round(x, 4) if instrument["display_currency"].upper() == "USD" else round(x, 3)


def _confidence_from_score(score: float) -> float:
    c = min(1.0, max(0.0, abs(score)))
    return round((c**0.75) * 100.0, 1)


def _success_from_alignment(score: float, alignment: int) -> float:
    base = 50 + (score * 25)
    bonus = alignment * 5
    return round(min(95.0, max(5.0, base + bonus)), 1)


def _limit_levels(price: float, atr: float, direction: str) -> tuple[float, float, float]:
    if atr <= 0 or math.isnan(atr):
        atr = max(0.05, price * 0.001)

    pullback = 0.25 * atr
    sl_buf = 1.2 * atr
    tp_buf = 2.0 * atr

    if direction == "BUY":
        entry = price - pullback
        sl = entry - sl_buf
        tp = entry + tp_buf
    else:
        entry = price + pullback
        sl = entry + sl_buf
        tp = entry - tp_buf

    return _round_fx(entry), _round_fx(sl), _round_fx(tp)


def _estimate_hours(distance: float, atr: float, interval_minutes: int) -> float | None:
    if atr <= 0:
        return None
    candles_needed = distance / atr
    return round((candles_needed * interval_minutes) / 60.0, 2)


def generate_signal() -> Signal:
    snap = get_market_snapshot()
    tech_s, ind = technical_score(snap.candles)
    news_s, news_items = get_news_sentiment()

    score = tech_s * settings.w_technical + news_s * settings.w_sentiment

    entry = stop_loss = take_profit = None
    action = "NEUTRAL"

    buy_alignment = sum(
        [
            ind["ema20"] > ind["ema50"],
            ind["macd_hist"] > 0,
            ind["rsi14"] > 50,
        ]
    )
    sell_alignment = sum(
        [
            ind["ema20"] < ind["ema50"],
            ind["macd_hist"] < 0,
            ind["rsi14"] < 50,
        ]
    )

    interval_minutes = int(settings.candle_interval.replace("m", "")) if "m" in settings.candle_interval else 15
    expected_entry_hours = None
    expected_tp_hours = None

    if score >= settings.score_buy and buy_alignment >= 2:
        action = "BUY LIMIT"
        entry, stop_loss, take_profit = _limit_levels(snap.price, ind.get("atr14", 0.0), "BUY")
        expected_entry_hours = _estimate_hours(abs(snap.price - entry), ind.get("atr14", 0.0), interval_minutes)
        expected_tp_hours = _estimate_hours(abs(take_profit - entry), ind.get("atr14", 0.0), interval_minutes)
        if (
            expected_entry_hours is None
            or expected_tp_hours is None
            or expected_entry_hours > settings.entry_horizon_hours
            or expected_tp_hours > settings.tp_horizon_hours
        ):
            action = "NEUTRAL"
            entry = stop_loss = take_profit = None
    elif score <= settings.score_sell and sell_alignment >= 2:
        action = "SELL LIMIT"
        entry, stop_loss, take_profit = _limit_levels(snap.price, ind.get("atr14", 0.0), "SELL")
        expected_entry_hours = _estimate_hours(abs(snap.price - entry), ind.get("atr14", 0.0), interval_minutes)
        expected_tp_hours = _estimate_hours(abs(entry - take_profit), ind.get("atr14", 0.0), interval_minutes)
        if (
            expected_entry_hours is None
            or expected_tp_hours is None
            or expected_entry_hours > settings.entry_horizon_hours
            or expected_tp_hours > settings.tp_horizon_hours
        ):
            action = "NEUTRAL"
            entry = stop_loss = take_profit = None

    confidence = _confidence_from_score(score)
    alignment = buy_alignment if action == "BUY LIMIT" else sell_alignment if action == "SELL LIMIT" else 0
    success_chance = _success_from_alignment(score, alignment)

    reason_parts = [
        (
            "Technik-Score: "
            f"{tech_s:+.2f} (RSI {ind['rsi14']:.1f}, EMA20 {ind['ema20']:.4f}, "
            f"EMA50 {ind['ema50']:.4f}, MACD-Hist {ind['macd_hist']:+.4f})"
        ),
        f"News-Sentiment: {news_s:+.2f} (RSS, lokal via VADER)",
        (
            "Kombinierter Score: "
            f"{score:+.2f} (Gewichtung Technik {settings.w_technical:.2f}, "
            f"News {settings.w_sentiment:.2f})"
        ),
    ]

    if expected_entry_hours is not None and expected_tp_hours is not None:
        reason_parts.append(
            f"Timing: Entry ~{expected_entry_hours}h, TP ~{expected_tp_hours}h (Limits: {settings.entry_horizon_hours}h/{settings.tp_horizon_hours}h)"
        )

    if snap.tv_summary and snap.tv_summary.get("recommendation"):
        reason_parts.append(f"TradingView-TA Zusatzinfo: {snap.tv_summary.get('recommendation')}")

    reason = " | ".join(reason_parts)

    return Signal(
        action=action,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
        success_chance=success_chance,
        score=score,
        reason=reason,
        details={
            "price": _round_fx(snap.price),
            "technical": ind,
            "tv": snap.tv_summary,
            "news": [
                {"title": n.title, "link": n.link, "source": n.source, "sentiment": n.sentiment}
                for n in news_items
            ],
            "news_sentiment": news_s,
            "technical_score": tech_s,
            "expected_entry_hours": expected_entry_hours,
            "expected_tp_hours": expected_tp_hours,
        },
    )
