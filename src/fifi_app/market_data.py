"""Market data providers and aggregation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import pandas as pd
import requests

from .config import AppConfig
from .logging_utils import get_logger

LOGGER = get_logger(__name__)


@dataclass
class PricePoint:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataProvider:
    """Abstract base class for market data providers."""

    def fetch_price_history(self, symbol: str) -> List[PricePoint]:
        raise NotImplementedError


class AlphaVantageProvider(MarketDataProvider):
    """Retrieve market data from Alpha Vantage API."""

    API_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key

    def fetch_price_history(self, symbol: str) -> List[PricePoint]:
        if not self.api_key:
            raise RuntimeError("Clé API Alpha Vantage manquante.")
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": self.api_key,
        }
        LOGGER.debug("Requête Alpha Vantage: %s", params)
        response = requests.get(self.API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get("Time Series (Daily)", {})
        price_points: List[PricePoint] = []
        for ts, values in data.items():
            price_points.append(
                PricePoint(
                    timestamp=datetime.fromisoformat(ts),
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=float(values["6. volume"]),
                )
            )
        return list(sorted(price_points, key=lambda p: p.timestamp))


class MockProvider(MarketDataProvider):
    """Fallback provider using synthetic data for testing."""

    def fetch_price_history(self, symbol: str) -> List[PricePoint]:  # noqa: D401 - part of interface
        LOGGER.warning("Utilisation de données de démonstration pour %s", symbol)
        now = datetime.utcnow()
        prices: List[PricePoint] = []
        base = 100.0
        for day in range(60):
            close = base + day * 0.5
            prices.append(
                PricePoint(
                    timestamp=now.replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta(days=day),
                    open=close - 0.5,
                    high=close + 1.0,
                    low=close - 1.0,
                    close=close,
                    volume=1000 + day * 10,
                )
            )
        return list(sorted(prices, key=lambda p: p.timestamp))


def to_dataframe(points: Iterable[PricePoint]) -> pd.DataFrame:
    """Convert price points to a pandas DataFrame."""

    rows = [
        {
            "timestamp": p.timestamp,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume,
        }
        for p in points
    ]
    df = pd.DataFrame(rows)
    df.set_index("timestamp", inplace=True)
    return df.sort_index()


def build_provider(config: AppConfig) -> MarketDataProvider:
    """Factory to select an appropriate provider."""

    alpha_key = config.api_keys.market_data.get("alpha_vantage")
    if alpha_key:
        return AlphaVantageProvider(alpha_key)
    return MockProvider()


__all__ = [
    "PricePoint",
    "MarketDataProvider",
    "AlphaVantageProvider",
    "MockProvider",
    "to_dataframe",
    "build_provider",
]
