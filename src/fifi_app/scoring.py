"""Composite scoring engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .config import AppConfig
from .fundamental import FundamentalSnapshot, score_fundamentals
from .sentiment import NewsItem, aggregate_sentiment
from .technical import score_technical


@dataclass
class AnalysisResult:
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    composite_score: float


def compute_scores(
    config: AppConfig,
    prices: pd.DataFrame,
    fundamentals: FundamentalSnapshot,
    news: Iterable[NewsItem],
) -> AnalysisResult:
    technical = score_technical(prices)
    fundamental = score_fundamentals(fundamentals)
    sentiment = aggregate_sentiment(news)

    weights = config.weights
    composite = (
        technical * weights.technical
        + fundamental * weights.fundamental
        + sentiment * weights.sentiment
    )

    return AnalysisResult(
        technical_score=technical,
        fundamental_score=fundamental,
        sentiment_score=sentiment,
        composite_score=composite,
    )


__all__ = ["AnalysisResult", "compute_scores"]
