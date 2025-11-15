"""Risk management helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .config import RiskConfig


@dataclass
class PositionSizingResult:
    capital_at_risk: float
    position_size: float
    stop_loss_price: float
    take_profit_price: float


def compute_position_size(
    capital: float,
    price: float,
    config: RiskConfig,
) -> PositionSizingResult:
    """Compute recommended position sizing based on risk settings."""

    capital_at_risk = capital * config.max_position_size_pct
    stop_loss_price = price * (1 - config.stop_loss_pct)
    take_profit_price = price * (1 + config.take_profit_pct)

    risk_per_unit = price - stop_loss_price
    if risk_per_unit <= 0:
        raise ValueError("Paramètres de stop-loss invalides")

    position_size = min(capital_at_risk / risk_per_unit, capital / price)

    return PositionSizingResult(
        capital_at_risk=capital_at_risk,
        position_size=position_size,
        stop_loss_price=stop_loss_price,
        take_profit_price=take_profit_price,
    )


__all__ = ["compute_position_size", "PositionSizingResult"]
