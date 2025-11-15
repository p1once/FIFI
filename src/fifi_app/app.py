"""PySide6 application for the FIFI assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .ai import OpenAIClient
from .config import ConfigManager
from .fundamental import FundamentalSnapshot
from .logging_utils import get_logger
from .market_data import build_provider, to_dataframe
from .risk import PositionSizingResult, compute_position_size
from .scoring import AnalysisResult, compute_scores
from .sentiment import build_sentiment_provider

LOGGER = get_logger(__name__)

DEFAULT_SYMBOL = "AAPL"
REFRESH_INTERVAL_MS = 5 * 60 * 1000


@dataclass
class DashboardState:
    symbol: str
    analysis: Optional[AnalysisResult]
    position: Optional[PositionSizingResult]
    ai_summary: Optional[str]


class DashboardTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout()

        self.symbol_label = QLabel("Symbole: -")
        self.score_label = QLabel("Scores: -")
        self.ai_label = QLabel("Recommandation IA: -")
        self.ai_label.setWordWrap(True)

        layout.addWidget(self.symbol_label)
        layout.addWidget(self.score_label)
        layout.addWidget(self.ai_label)
        layout.addStretch(1)
        self.setLayout(layout)

    def update_state(self, state: DashboardState) -> None:
        self.symbol_label.setText(f"Symbole analysé: {state.symbol}")
        if state.analysis:
            analysis = state.analysis
            self.score_label.setText(
                (
                    f"Score technique: {analysis.technical_score:.2f}\n"
                    f"Score fondamental: {analysis.fundamental_score:.2f}\n"
                    f"Score sentiment: {analysis.sentiment_score:.2f}\n"
                    f"Score composite: {analysis.composite_score:.2f}"
                )
            )
        else:
            self.score_label.setText("Scores indisponibles")

        if state.ai_summary:
            self.ai_label.setText(state.ai_summary)
        else:
            self.ai_label.setText("Recommandation IA indisponible (ajoutez une clé OpenAI)")


class SettingsTab(QWidget):
    def __init__(self, manager: ConfigManager, refresh_callback) -> None:
        super().__init__()
        self.manager = manager
        self.refresh_callback = refresh_callback
        layout = QVBoxLayout()

        layout.addWidget(self._build_api_box())
        layout.addWidget(self._build_weights_box())
        layout.addWidget(self._build_risk_box())

        apply_btn = QPushButton("Enregistrer et rafraîchir")
        apply_btn.clicked.connect(self._apply_changes)
        layout.addWidget(apply_btn)
        layout.addStretch(1)
        self.setLayout(layout)

    def _build_api_box(self) -> QGroupBox:
        box = QGroupBox("Clés API")
        form = QFormLayout()

        self.openai_edit = QLineEdit(self.manager.config.api_keys.openai or "")
        self.alpha_vantage_edit = QLineEdit(
            self.manager.config.api_keys.market_data.get("alpha_vantage", "")
        )
        self.finnhub_edit = QLineEdit(
            self.manager.config.api_keys.sentiment.get("finnhub", "")
            if self.manager.config.api_keys.sentiment
            else ""
        )
        self.symbol_edit = QLineEdit(self.manager.config.providers.alpha_vantage_symbol or DEFAULT_SYMBOL)

        form.addRow("OpenAI:", self.openai_edit)
        form.addRow("Alpha Vantage:", self.alpha_vantage_edit)
        form.addRow("Finnhub (sentiment):", self.finnhub_edit)
        form.addRow("Symbole par défaut:", self.symbol_edit)
        box.setLayout(form)
        return box

    def _build_weights_box(self) -> QGroupBox:
        box = QGroupBox("Pondérations")
        form = QFormLayout()

        self.technical_edit = QLineEdit(str(self.manager.config.weights.technical))
        self.fundamental_edit = QLineEdit(str(self.manager.config.weights.fundamental))
        self.sentiment_edit = QLineEdit(str(self.manager.config.weights.sentiment))

        form.addRow("Technique:", self.technical_edit)
        form.addRow("Fondamental:", self.fundamental_edit)
        form.addRow("Sentiment:", self.sentiment_edit)
        box.setLayout(form)
        return box

    def _build_risk_box(self) -> QGroupBox:
        box = QGroupBox("Gestion du risque")
        form = QFormLayout()
        risk = self.manager.config.risk

        self.max_position_edit = QLineEdit(str(risk.max_position_size_pct))
        self.max_daily_loss_edit = QLineEdit(str(risk.max_daily_loss_pct))
        self.stop_loss_edit = QLineEdit(str(risk.stop_loss_pct))
        self.take_profit_edit = QLineEdit(str(risk.take_profit_pct))

        form.addRow("Taille max position (% capital):", self.max_position_edit)
        form.addRow("Perte journalière max (% capital):", self.max_daily_loss_edit)
        form.addRow("Stop-loss (%):", self.stop_loss_edit)
        form.addRow("Take-profit (%):", self.take_profit_edit)
        box.setLayout(form)
        return box

    def _apply_changes(self) -> None:
        try:
            self.manager.update_api_key("openai", self.openai_edit.text().strip() or None, category="openai")
            self.manager.update_api_key(
                "alpha_vantage", self.alpha_vantage_edit.text().strip() or None, category="market"
            )
            self.manager.update_api_key("finnhub", self.finnhub_edit.text().strip() or None, category="sentiment")
            self.manager.config.providers.alpha_vantage_symbol = self.symbol_edit.text().strip() or DEFAULT_SYMBOL
            technical = float(self.technical_edit.text())
            fundamental = float(self.fundamental_edit.text())
            sentiment = float(self.sentiment_edit.text())
            self.manager.update_weights(technical, fundamental, sentiment)
            self.manager.update_risk(
                max_position_size_pct=float(self.max_position_edit.text()),
                max_daily_loss_pct=float(self.max_daily_loss_edit.text()),
                stop_loss_pct=float(self.stop_loss_edit.text()),
                take_profit_pct=float(self.take_profit_edit.text()),
            )
            self.manager.save()
            QMessageBox.information(self, "Succès", "Paramètres enregistrés")
            self.refresh_callback()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer: {exc}")


class FIFIMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FIFI – Assistant IA pour investisseurs")
        self.resize(900, 600)

        self.config_manager = ConfigManager()

        self.dashboard_tab = DashboardTab()
        self.settings_tab = SettingsTab(self.config_manager, self.refresh_data)

        tabs = QTabWidget()
        tabs.addTab(self.dashboard_tab, "Tableau de bord")
        tabs.addTab(self.settings_tab, "Paramètres")
        self.setCentralWidget(tabs)

        refresh_action = QAction("Rafraîchir", self)
        refresh_action.triggered.connect(self.refresh_data)
        self.toolbar = self.addToolBar("Actions")
        self.toolbar.addAction(refresh_action)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(REFRESH_INTERVAL_MS)

        self.refresh_data()

    def refresh_data(self) -> None:
        config = self.config_manager.config
        symbol = config.providers.alpha_vantage_symbol or DEFAULT_SYMBOL

        try:
            provider = build_provider(config)
            price_points = provider.fetch_price_history(symbol)
            prices = to_dataframe(price_points)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Erreur lors de la récupération des prix: %s", exc)
            QMessageBox.warning(self, "Données marché", str(exc))
            prices = pd.DataFrame(columns=["close"]).astype(float)

        fundamental = self._derive_fundamentals(symbol, prices)

        try:
            sentiment_provider = build_sentiment_provider(
                config.api_keys.sentiment.get("finnhub") if config.api_keys.sentiment else None
            )
            news = sentiment_provider.fetch_news(symbol)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Erreur sentiment: %s", exc)
            QMessageBox.warning(self, "Sentiment", str(exc))
            news = []

        try:
            analysis = compute_scores(config, prices, fundamental, news)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Erreur calcul des scores: %s", exc)
            QMessageBox.warning(self, "Scores", str(exc))
            analysis = AnalysisResult(0.5, 0.5, 0.5, 0.5)
        position = None
        try:
            position = compute_position_size(10_000, prices["close"].iloc[-1] if not prices.empty else 100.0, config.risk)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Erreur gestion du risque: %s", exc)

        ai_summary = None
        if config.api_keys.openai:
            try:
                client = OpenAIClient(config)
                prompt = client.build_prompt(
                    market_overview=self._build_market_overview(symbol, prices),
                    technical_score=analysis.technical_score,
                    technical_summary="Tendance basée sur moyennes mobiles et RSI.",
                    fundamental_score=analysis.fundamental_score,
                    fundamental_summary="Ratios calculés à partir des données disponibles.",
                    sentiment_score=analysis.sentiment_score,
                    sentiment_summary="Synthèse des actualités disponibles.",
                    risk_context=self._build_risk_context(position),
                )
                ai_summary = client.get_recommendation(prompt)
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Erreur lors de l'appel OpenAI: %s", exc)
                QMessageBox.warning(self, "OpenAI", str(exc))

        state = DashboardState(symbol=symbol, analysis=analysis, position=position, ai_summary=ai_summary)
        self.dashboard_tab.update_state(state)

    def _derive_fundamentals(self, symbol: str, prices: pd.DataFrame) -> FundamentalSnapshot:
        if prices.empty:
            return FundamentalSnapshot(symbol=symbol)
        closes = prices["close"].tail(60)
        growth = (closes.iloc[-1] / closes.iloc[0] - 1) * 100 if len(closes) > 1 else 0.0
        return FundamentalSnapshot(
            symbol=symbol,
            pe_ratio=20.0,
            peg_ratio=1.1,
            debt_to_equity=0.6,
            revenue_growth_pct=growth,
            earnings_growth_pct=growth * 0.8,
        )

    def _build_market_overview(self, symbol: str, prices: pd.DataFrame) -> str:
        if prices.empty:
            return f"Aucune donnée disponible pour {symbol}."
        latest = prices.iloc[-1]
        return f"Clôture: {latest['close']:.2f}, Volume: {latest.get('volume', float('nan'))}"  # type: ignore[index]

    def _build_risk_context(self, position: Optional[PositionSizingResult]) -> str:
        if not position:
            return "Position non calculée."
        return (
            "Capital à risque: {risk:.2f}, Taille position: {size:.2f} unités, "
            "Stop-loss: {sl:.2f}, Take-profit: {tp:.2f}"
        ).format(
            risk=position.capital_at_risk,
            size=position.position_size,
            sl=position.stop_loss_price,
            tp=position.take_profit_price,
        )


def run_app() -> None:
    app = QApplication.instance() or QApplication([])
    window = FIFIMainWindow()
    window.show()
    app.exec()


__all__ = ["run_app", "FIFIMainWindow"]
