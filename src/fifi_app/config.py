"""Configuration management for the FIFI application."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError, validator

from .logging_utils import get_logger

LOGGER = get_logger(__name__)


APP_DIR_NAME = "fifi-app"
CONFIG_FILE_NAME = "config.json"


class WeightConfig(BaseModel):
    """Weights for the composite score."""

    technical: float = Field(default=0.6, ge=0.0, le=1.0)
    fundamental: float = Field(default=0.25, ge=0.0, le=1.0)
    sentiment: float = Field(default=0.15, ge=0.0, le=1.0)

    @validator("sentiment")
    def _ensure_total(cls, v: float, values: Dict[str, Any]) -> float:  # noqa: D401
        """Ensure weights sum to 1."""
        total = v + values.get("technical", 0.0) + values.get("fundamental", 0.0)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("La somme des pondérations doit être égale à 1.0")
        return v


class NotificationConfig(BaseModel):
    """Configuration for notifications."""

    email: Optional[str] = None
    desktop_alerts: bool = True
    webhook_url: Optional[str] = None


class ApiKeys(BaseModel):
    """Holds API keys for external services."""

    openai: Optional[str] = None
    market_data: Dict[str, str] = Field(default_factory=dict)
    sentiment: Dict[str, str] = Field(default_factory=dict)


class DataProviderConfig(BaseModel):
    """Configuration per data provider."""

    alpha_vantage_symbol: Optional[str] = None
    finnhub_symbol: Optional[str] = None
    update_interval_minutes: int = Field(default=5, ge=1)


class RiskConfig(BaseModel):
    """Risk management parameters."""

    max_position_size_pct: float = Field(default=0.05, ge=0.0, le=1.0)
    max_daily_loss_pct: float = Field(default=0.02, ge=0.0, le=1.0)
    stop_loss_pct: float = Field(default=0.03, ge=0.0, le=1.0)
    take_profit_pct: float = Field(default=0.06, ge=0.0, le=1.0)


class AppConfig(BaseModel):
    """Top-level configuration for the app."""

    weights: WeightConfig = Field(default_factory=WeightConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    api_keys: ApiKeys = Field(default_factory=ApiKeys)
    providers: DataProviderConfig = Field(default_factory=DataProviderConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)


class ConfigManager:
    """Manage configuration persistence and updates."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self.config_dir = config_dir or self._default_config_dir()
        self.config_path = self.config_dir / CONFIG_FILE_NAME
        self._config: AppConfig = AppConfig()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    @staticmethod
    def _default_config_dir() -> Path:
        """Return platform-specific configuration directory."""
        if os.name == "nt":
            root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return root / APP_DIR_NAME

    @property
    def config(self) -> AppConfig:
        return self._config

    def load(self) -> None:
        if not self.config_path.exists():
            LOGGER.info("Aucune configuration trouvée, création d'un fichier par défaut.")
            self.save()
            return
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            self._config = AppConfig(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            LOGGER.error("Erreur lors du chargement de la configuration: %s", exc)
            self._config = AppConfig()

    def save(self) -> None:
        self.config_path.write_text(self._config.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")

    def update_api_key(self, service: str, value: Optional[str], category: str = "market") -> None:
        LOGGER.info("Mise à jour de la clé API pour %s (%s)", service, category)
        if category == "openai" or service == "openai":
            self._config.api_keys.openai = value
        elif category == "sentiment":
            if value:
                self._config.api_keys.sentiment[service] = value
            else:
                self._config.api_keys.sentiment.pop(service, None)
        else:
            if value:
                self._config.api_keys.market_data[service] = value
            else:
                self._config.api_keys.market_data.pop(service, None)
        self.save()

    def update_weights(self, technical: float, fundamental: float, sentiment: float) -> None:
        LOGGER.info("Mise à jour des pondérations: T=%s F=%s S=%s", technical, fundamental, sentiment)
        self._config.weights = WeightConfig(technical=technical, fundamental=fundamental, sentiment=sentiment)
        self.save()

    def update_risk(self, **kwargs: Any) -> None:
        LOGGER.info("Mise à jour des paramètres de risque: %s", kwargs)
        updated = self._config.risk.model_copy(update=kwargs)
        self._config.risk = RiskConfig(**updated.model_dump())
        self.save()


__all__ = [
    "AppConfig",
    "ConfigManager",
]
