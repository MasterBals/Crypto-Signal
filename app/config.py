from dataclasses import asdict, dataclass
import json
import os
from typing import Any


DEFAULT_SETTINGS_PATH = os.getenv("SETTINGS_PATH", "/app/data/settings.json")


@dataclass
class Settings:
    pair_symbol_yf: str = "EURJPY=X"
    tz: str = "Europe/Zurich"

    history_days: int = 20
    candle_interval: str = "15m"

    refresh_seconds: int = 300

    rss_urls: tuple[str, ...] = (
        "https://www.forexlive.com/feed/",
        "https://www.fxstreet.com/rss/news",
        "https://www.investing.com/rss/news_285.rss",
    )

    w_technical: float = 0.70
    w_sentiment: float = 0.30

    score_buy: float = 0.35
    score_sell: float = -0.35

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rss_urls"] = list(self.rss_urls)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        payload = dict(data)
        if "rss_urls" in payload and isinstance(payload["rss_urls"], list):
            payload["rss_urls"] = tuple(payload["rss_urls"])
        return cls(**payload)


def load_settings(path: str = DEFAULT_SETTINGS_PATH) -> Settings:
    if not os.path.exists(path):
        return Settings()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return Settings.from_dict(data)
    except Exception:
        return Settings()


def save_settings(settings: Settings, path: str = DEFAULT_SETTINGS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings.to_dict(), handle, indent=2, ensure_ascii=False)


def update_settings(payload: dict[str, Any]) -> Settings:
    global settings
    settings = Settings.from_dict(payload)
    save_settings(settings)
    return settings


def get_settings() -> Settings:
    return settings


settings = load_settings()
