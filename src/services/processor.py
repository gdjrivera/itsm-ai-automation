import json
import logging
from typing import Any

from src.ai.llm_client import OllamaClient
from src.ai.prompts import (
    SYSTEM_CLASSIFY,
    SYSTEM_RESOLUTION,
    classify_ticket_prompt,
    suggest_resolution_prompt,
)
from src.models.ticket import Ticket

logger = logging.getLogger(__name__)


class TicketProcessor:
    def __init__(self, llm: OllamaClient) -> None:
        self._llm = llm

    async def classify(self, ticket: Ticket) -> dict[str, Any]:
        prompt = classify_ticket_prompt(ticket.title, ticket.description)
        result = await self._llm.generate(
            prompt=prompt,
            system=SYSTEM_CLASSIFY,
            temperature=0.1,
            max_tokens=256,
        )
        try:
            return json.loads(result.content)
        except json.JSONDecodeError:
            logger.error("classify: invalid JSON from LLM — %s", result.content[:200])
            return {"category": "incident", "priority": "medium", "confidence": 0.0}

    async def suggest_resolution(self, ticket: Ticket) -> dict[str, Any]:
        prompt = suggest_resolution_prompt(ticket.summary())
        result = await self._llm.generate(
            prompt=prompt,
            system=SYSTEM_RESOLUTION,
            temperature=0.2,
            max_tokens=512,
        )
        try:
            return json.loads(result.content)
        except json.JSONDecodeError:
            logger.error("resolution: invalid JSON from LLM — %s", result.content[:200])
            return {"causa_raiz": "No determinada", "accion": "Revisar manualmente", "tiempo_estimado": 30, "requiere_escalar": True}

    async def process(self, ticket: Ticket) -> dict[str, Any]:
        classification, resolution = await self.classify(ticket), await self.suggest_resolution(ticket)
        return {
            "ticket_id": ticket.id,
            "classification": classification,
            "resolution_suggestion": resolution,
            "requires_escalation": resolution.get("requiere_escalar", False),
        }
