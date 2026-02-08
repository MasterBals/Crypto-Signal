from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math

from app.config import settings
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
    score: float
    reason: str
    details: dict[str, Any]


def _round_fx(x: float) -> float:
    return round(x, 3)


def _confidence_from_score(score: float) -> float:
    c = min(1.0, max(0.0, abs(score)))
    return round((c**0.75) * 100.0, 1)


def _limit_levels(price: float, atr: float, direction: str) -> tuple[float, float, float]:
    """
    Konservative Limit-Order-Logik:
    - Entry nicht Market, sondern Pullback (0.25 ATR)
    - SL mit Reserve (1.2 ATR) gegen typische Dips
    - TP mit Chance/Risiko ca. 2:1 (2.0 * ATR)
    """
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


def generate_signal() -> Signal:
    snap = get_market_snapshot()
    tech_s, ind = technical_score(snap.candles)
    news_s, news_items = get_news_sentiment()

    score = tech_s * settings.w_technical + news_s * settings.w_sentiment

    entry = stop_loss = take_profit = None

    if score >= settings.score_buy:
        action = "BUY LIMIT"
        entry, stop_loss, take_profit = _limit_levels(snap.price, ind.get("atr14", 0.0), "BUY")
    elif score <= settings.score_sell:
        action = "SELL LIMIT"
        entry, stop_loss, take_profit = _limit_levels(snap.price, ind.get("atr14", 0.0), "SELL")
    else:
        action = "NEUTRAL"

    confidence = _confidence_from_score(score)

    reason_parts = [
        (
            "Technik-Score: "
            f"{tech_s:+.2f} (RSI {ind['rsi14']:.1f}, EMA20 {ind['ema20']:.3f}, "
            f"EMA50 {ind['ema50']:.3f}, MACD-Hist {ind['macd_hist']:+.4f})"
        ),
        f"News-Sentiment: {news_s:+.2f} (RSS, lokal via VADER)",
        (
            "Kombinierter Score: "
            f"{score:+.2f} (Gewichtung Technik {settings.w_technical:.2f}, "
            f"News {settings.w_sentiment:.2f})"
        ),
    ]

    if snap.tv_summary and snap.tv_summary.get("recommendation"):
        reason_parts.append(f"TradingView-TA Zusatzinfo: {snap.tv_summary.get('recommendation')}")

    reason = " | ".join(reason_parts)

    return Signal(
        action=action,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
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
        },
    )
