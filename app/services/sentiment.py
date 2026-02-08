from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def vader_compound(text: str) -> float:
    if not text:
        return 0.0
    vs = _analyzer.polarity_scores(text)
    return float(vs.get("compound", 0.0))
