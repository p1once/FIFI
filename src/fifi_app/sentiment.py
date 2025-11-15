"""Sentiment analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

from .logging_utils import get_logger

LOGGER = get_logger(__name__)


@dataclass
class NewsItem:
    title: str
    summary: str
    sentiment: float  # -1 to 1
    source: str
    url: str


class SentimentProvider:
    """Base class for sentiment providers."""

    def fetch_news(self, symbol: str) -> List[NewsItem]:
        raise NotImplementedError


class FinnhubSentiment(SentimentProvider):
    """Retrieve sentiment from Finnhub news API."""

    API_URL = "https://finnhub.io/api/v1/news-sentiment"

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key

    def fetch_news(self, symbol: str) -> List[NewsItem]:
        if not self.api_key:
            raise RuntimeError("Clé API Finnhub manquante")
        params = {"symbol": symbol, "token": self.api_key}
        response = requests.get(self.API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        news = []
        for item in payload.get("sentiment", []):
            news.append(
                NewsItem(
                    title=item.get("headline", ""),
                    summary=item.get("summary", ""),
                    sentiment=float(item.get("sentiment", 0.0)),
                    source=item.get("source", "finnhub"),
                    url=item.get("url", ""),
                )
            )
        return news


class MockSentiment(SentimentProvider):
    """Fallback provider with neutral sentiment."""

    def fetch_news(self, symbol: str) -> List[NewsItem]:  # noqa: D401
        LOGGER.warning("Aucun fournisseur de sentiment configuré, utilisation d'une valeur neutre.")
        return [
            NewsItem(
                title=f"Sentiment neutre pour {symbol}",
                summary="Configurez une clé API pour obtenir des analyses en temps réel.",
                sentiment=0.0,
                source="mock",
                url="",
            )
        ]


def aggregate_sentiment(items: Iterable[NewsItem]) -> float:
    """Aggregate sentiment score between 0 and 1."""

    items = list(items)
    if not items:
        return 0.5
    normalized = [(item.sentiment + 1) / 2 for item in items]
    return sum(normalized) / len(normalized)


def build_sentiment_provider(api_key: Optional[str]) -> SentimentProvider:
    if api_key:
        return FinnhubSentiment(api_key)
    return MockSentiment()


__all__ = [
    "NewsItem",
    "SentimentProvider",
    "FinnhubSentiment",
    "MockSentiment",
    "aggregate_sentiment",
    "build_sentiment_provider",
]
