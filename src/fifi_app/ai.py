"""OpenAI client abstraction."""

from __future__ import annotations

from typing import List

from openai import OpenAI

from .config import AppConfig
from .logging_utils import get_logger

LOGGER = get_logger(__name__)

PROMPT_TEMPLATE = """Tu es un assistant financier prudent. Analyse les informations suivantes et propose une recommandation.

Données de marché:
{market_overview}

Analyse technique (score: {technical_score:.2f}):
{technical_summary}

Analyse fondamentale (score: {fundamental_score:.2f}):
{fundamental_summary}

Analyse de sentiment (score: {sentiment_score:.2f}):
{sentiment_summary}

Contraintes de risque:
{risk_context}

Réponds en français, avec un ton prudent. Fournis:
- Une conclusion (achat, vente, neutre) avec justification
- Les risques majeurs
- Des actions possibles (ex: ajuster stop-loss)
"""


class OpenAIClient:
    """Wrapper around the OpenAI SDK."""

    def __init__(self, config: AppConfig) -> None:
        if not config.api_keys.openai:
            raise RuntimeError("Clé API OpenAI manquante.")
        self.client = OpenAI(api_key=config.api_keys.openai)

    def build_prompt(
        self,
        market_overview: str,
        technical_score: float,
        technical_summary: str,
        fundamental_score: float,
        fundamental_summary: str,
        sentiment_score: float,
        sentiment_summary: str,
        risk_context: str,
    ) -> str:
        return PROMPT_TEMPLATE.format(
            market_overview=market_overview,
            technical_score=technical_score,
            technical_summary=technical_summary,
            fundamental_score=fundamental_score,
            fundamental_summary=fundamental_summary,
            sentiment_score=sentiment_score,
            sentiment_summary=sentiment_summary,
            risk_context=risk_context,
        )

    def get_recommendation(self, prompt: str) -> str:
        LOGGER.info("Appel à l'API OpenAI pour une recommandation.")
        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        text_parts: List[str] = []
        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if content.type == "text":
                        text_parts.append(content.text)
        return "\n".join(text_parts)


__all__ = ["OpenAIClient", "PROMPT_TEMPLATE"]
