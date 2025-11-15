"""Technical analysis helpers."""

from __future__ import annotations

import pandas as pd


def moving_average(df: pd.DataFrame, window: int) -> pd.Series:
    return df["close"].rolling(window=window, min_periods=window).mean()


def relative_strength_index(df: pd.DataFrame, window: int = 14) -> pd.Series:
    delta = df["close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.rolling(window=window, min_periods=window).mean()
    roll_down = down.rolling(window=window, min_periods=window).mean()
    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    ma = moving_average(df, window)
    std = df["close"].rolling(window=window, min_periods=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return pd.DataFrame({"ma": ma, "upper": upper, "lower": lower})


def score_technical(df: pd.DataFrame) -> float:
    """Compute a technical score between 0 and 1."""

    if df.empty:
        return 0.5

    latest = df.iloc[-1]
    ma_short = moving_average(df, 20).iloc[-1]
    ma_long = moving_average(df, 50).iloc[-1]
    rsi = relative_strength_index(df).iloc[-1]
    boll = bollinger_bands(df).iloc[-1]

    score = 0.0
    weight = 0.0

    if pd.notna(ma_short) and pd.notna(ma_long):
        trend = 1.0 if ma_short > ma_long else 0.0
        score += trend
        weight += 1.0

    if pd.notna(rsi):
        if 40 <= rsi <= 60:
            score += 0.5
        elif rsi < 30:
            score += 0.8
        elif rsi > 70:
            score += 0.2
        else:
            score += 0.6
        weight += 1.0

    price = latest["close"]
    lower = boll["lower"]
    upper = boll["upper"]
    if pd.notna(lower) and pd.notna(upper) and upper != lower:
        position = (price - lower) / (upper - lower)
        score += max(0.0, min(1.0, 1 - position))
        weight += 1.0

    if weight == 0:
        return 0.5
    return float(max(0.0, min(1.0, score / weight)))


__all__ = [
    "moving_average",
    "relative_strength_index",
    "bollinger_bands",
    "score_technical",
]
