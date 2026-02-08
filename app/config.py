from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS_PATH = os.getenv("SETTINGS_PATH", "/app/data/settings.json")

INSTRUMENTS: dict[str, dict[str, Any]] = {
    "eurjpy": {
        "key": "eurjpy",
        "label": "EUR/JPY",
        "symbol": "EURJPY=X",
        "display_currency": "JPY",
        "news_keywords": ["eur", "jpy", "yen", "euro", "boj", "ecb"],
    },
    "usdjpy": {
        "key": "usdjpy",
        "label": "USD/JPY",
        "symbol": "JPY=X",
        "display_currency": "JPY",
        "news_keywords": ["usd", "jpy", "yen", "boj", "fed"],
    },
    "btcusd": {
        "key": "btcusd",
        "label": "BTC/USD",
        "symbol": "BTC-USD",
        "display_currency": "USD",
        "news_keywords": ["bitcoin", "btc", "crypto"],
    },
}


@dataclass
class Settings:
    instrument_key: str = "eurjpy"
    tz: str = "Europe/Zurich"
    history_days: int = 60
    candle_interval: str = "15m"
    refresh_seconds: int = 300
    entry_horizon_hours: float = 6.0
    tp_horizon_hours: float = 24.0
    w_technical: float = 0.7
    w_sentiment: float = 0.3
    score_buy: float = 0.25
    score_sell: float = -0.25
    rss_urls: list[str] = field(
        default_factory=lambda: [
            "https://www.fxstreet.com/rss/news",
            "https://www.reutersagency.com/feed/?best-topics=forex",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_key": self.instrument_key,
            "tz": self.tz,
            "history_days": self.history_days,
            "candle_interval": self.candle_interval,
            "refresh_seconds": self.refresh_seconds,
            "entry_horizon_hours": self.entry_horizon_hours,
            "tp_horizon_hours": self.tp_horizon_hours,
            "w_technical": self.w_technical,
            "w_sentiment": self.w_sentiment,
            "score_buy": self.score_buy,
            "score_sell": self.score_sell,
            "rss_urls": list(self.rss_urls),
        }


def _load_settings_from_disk() -> dict[str, Any]:
    path = Path(DEFAULT_SETTINGS_PATH)
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def _save_settings_to_disk(payload: dict[str, Any]) -> None:
    path = Path(DEFAULT_SETTINGS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _apply_settings(settings: Settings, raw: dict[str, Any]) -> None:
    settings.instrument_key = raw.get("instrument_key", settings.instrument_key)
    settings.tz = raw.get("tz", settings.tz)
    settings.history_days = int(raw.get("history_days", settings.history_days))
    settings.candle_interval = raw.get("candle_interval", settings.candle_interval)
    settings.refresh_seconds = int(raw.get("refresh_seconds", settings.refresh_seconds))
    settings.entry_horizon_hours = float(raw.get("entry_horizon_hours", settings.entry_horizon_hours))
    settings.tp_horizon_hours = float(raw.get("tp_horizon_hours", settings.tp_horizon_hours))
    settings.w_technical = float(raw.get("w_technical", settings.w_technical))
    settings.w_sentiment = float(raw.get("w_sentiment", settings.w_sentiment))
    settings.score_buy = float(raw.get("score_buy", settings.score_buy))
    settings.score_sell = float(raw.get("score_sell", settings.score_sell))
    settings.rss_urls = list(raw.get("rss_urls", settings.rss_urls))


def load_settings() -> Settings:
    raw = _load_settings_from_disk()
    settings = Settings()
    if not raw:
        return settings
    _apply_settings(settings, raw)
    return settings


def save_settings(payload: dict[str, Any]) -> Settings:
    _apply_settings(settings, payload)
    _save_settings_to_disk(settings.to_dict())
    return settings


settings = load_settings()


def list_instruments() -> list[dict[str, Any]]:
    return [instrument.copy() for instrument in INSTRUMENTS.values()]


def get_instrument() -> dict[str, Any]:
    instrument = INSTRUMENTS.get(settings.instrument_key)
    if instrument:
        return instrument
    return INSTRUMENTS["eurjpy"]
