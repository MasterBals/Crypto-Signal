from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.services.sentiment import vader_compound


@dataclass
class NewsItem:
    title: str
    link: str
    source: str
    sentiment: float


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _fetch_rss(url: str, timeout: int = 10) -> list[dict[str, Any]]:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "eurjpy-ai-dashboard/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    items: list[dict[str, Any]] = []
    for it in soup.find_all("item")[:20]:
        title = _clean_text(it.title.get_text() if it.title else "")
        link = _clean_text(it.link.get_text() if it.link else "")
        items.append({"title": title, "link": link})
    return items


def _is_relevant(title: str) -> bool:
    t = title.lower()
    keys = [
        "eur",
        "euro",
        "ecb",
        "jpy",
        "yen",
        "japan",
        "boj",
        "rate",
        "rates",
        "inflation",
        "cpi",
        "gdp",
        "bond",
        "yield",
        "central bank",
        "interest",
        "hawkish",
        "dovish",
        "policy",
        "fx",
        "forex",
    ]
    return any(k in t for k in keys)


def get_news_sentiment(max_items: int = 12) -> tuple[float, list[NewsItem]]:
    """
    Liefert:
    - aggregiertes Sentiment in [-1..+1]
    - NewsItem-Liste
    """
    items: list[NewsItem] = []
    sentiments: list[float] = []

    for url in settings.rss_urls:
        try:
            raw = _fetch_rss(url)
            src = url.split("/")[2] if "://" in url else url
            for it in raw:
                title = it.get("title", "")
                if not title or not _is_relevant(title):
                    continue
                s = vader_compound(title)
                items.append(NewsItem(title=title, link=it.get("link", ""), source=src, sentiment=s))
                sentiments.append(s)
        except Exception:
            continue

    items.sort(key=lambda x: abs(x.sentiment), reverse=True)
    items = items[:max_items]

    if sentiments:
        agg = sum(sentiments) / max(1, len(sentiments))
        agg = max(-1.0, min(1.0, agg))
    else:
        agg = 0.0

    return agg, items
