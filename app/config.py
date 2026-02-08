from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    pair_symbol_yf: str = "EURJPY=X"
    tz: str = "Europe/Zurich"

    # Chart history
    history_days: int = 20  # genug fuer Indikatoren und ATR
    candle_interval: str = "15m"  # 15 Minuten als praxisnahe Basis

    # Background refresh
    refresh_seconds: int = 300  # 5 Minuten

    # RSS Feeds (kostenfrei)
    # Hinweis: RSS-Qualitaet schwankt, daher mehrere Quellen.
    rss_urls: tuple[str, ...] = (
        "https://www.forexlive.com/feed/",
        "https://www.fxstreet.com/rss/news",
        "https://www.investing.com/rss/news_285.rss",
    )

    # Gewichtung
    w_technical: float = 0.70
    w_sentiment: float = 0.30

    # Signal-Schwellen
    score_buy: float = 0.35
    score_sell: float = -0.35


settings = Settings()
