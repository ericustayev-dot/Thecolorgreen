"""Score headline sentiment using VADER (a simple, rule-based sentiment tool),
and surface the single most extreme headline as a likely catalyst."""

from typing import Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def score_headline(text: str) -> float:
    """Returns a compound score from -1 (very negative) to +1 (very positive)."""
    return _analyzer.polarity_scores(text)["compound"]


def label_for_score(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def score_headlines(headlines: list[dict]) -> list[dict]:
    """headlines: list of dicts with a 'title' key. Returns the same dicts with
    'sentiment_score' and 'sentiment_label' attached."""
    scored = []
    for h in headlines:
        score = score_headline(h["title"])
        scored.append({**h, "sentiment_score": score, "sentiment_label": label_for_score(score)})
    return scored


def average_sentiment(scored_headlines: list[dict]) -> dict:
    if not scored_headlines:
        return {"average_score": 0.0, "label": "neutral"}

    scores = [h["sentiment_score"] for h in scored_headlines]
    avg = sum(scores) / len(scores)
    return {"average_score": round(avg, 3), "label": label_for_score(avg)}


def find_catalyst(scored_headlines: list[dict]) -> Optional[dict]:
    """The headline with the strongest sentiment in either direction -
    a heuristic guess at what's driving the news, not a confirmed cause."""
    if not scored_headlines:
        return None
    return max(scored_headlines, key=lambda h: abs(h["sentiment_score"]))


def find_bearish_driver(scored_headlines: list[dict]) -> Optional[dict]:
    """The most negative headline, if any headline is actually negative."""
    if not scored_headlines:
        return None
    most_negative = min(scored_headlines, key=lambda h: h["sentiment_score"])
    return most_negative if most_negative["sentiment_score"] < -0.05 else None


def find_bullish_driver(scored_headlines: list[dict]) -> Optional[dict]:
    """The most positive headline, if any headline is actually positive."""
    if not scored_headlines:
        return None
    most_positive = max(scored_headlines, key=lambda h: h["sentiment_score"])
    return most_positive if most_positive["sentiment_score"] > 0.05 else None


def split_by_sentiment(scored_headlines: list[dict]) -> dict:
    """Groups headlines into positive/neutral/negative buckets, each sorted
    by how strongly they lean that way."""
    groups = {"positive": [], "neutral": [], "negative": []}
    for h in scored_headlines:
        groups[h["sentiment_label"]].append(h)

    groups["positive"].sort(key=lambda h: h["sentiment_score"], reverse=True)
    groups["negative"].sort(key=lambda h: h["sentiment_score"])
    return groups
