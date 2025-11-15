"""Fundamental analysis helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .logging_utils import get_logger

LOGGER = get_logger(__name__)


@dataclass
class FundamentalSnapshot:
    symbol: str
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_growth_pct: Optional[float] = None
    earnings_growth_pct: Optional[float] = None


def score_fundamentals(snapshot: FundamentalSnapshot) -> float:
    """Return a normalized score between 0 and 1."""

    score = 0.0
    weight = 0.0

    def add(metric: Optional[float], ideal: float, tolerance: float) -> None:
        nonlocal score, weight
        if metric is None:
            return
        deviation = max(0.0, 1.0 - abs(metric - ideal) / tolerance)
        score += deviation
        weight += 1.0

    add(snapshot.pe_ratio, 20.0, 15.0)
    add(snapshot.peg_ratio, 1.0, 1.0)
    add(snapshot.debt_to_equity, 0.5, 0.7)

    if snapshot.revenue_growth_pct is not None:
        score += min(1.0, snapshot.revenue_growth_pct / 20.0)
        weight += 1.0
    if snapshot.earnings_growth_pct is not None:
        score += min(1.0, snapshot.earnings_growth_pct / 20.0)
        weight += 1.0

    if weight == 0:
        LOGGER.warning("Aucune donnée fondamentale disponible pour %s", snapshot.symbol)
        return 0.5
    return max(0.0, min(1.0, score / weight))


__all__ = [
    "FundamentalSnapshot",
    "score_fundamentals",
]
