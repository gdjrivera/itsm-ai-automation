import asyncio
import logging

from src.config.settings import get_settings
from src.connectors.base import ITSMConnector
from src.connectors.freshservice import FreshserviceConnector
from src.connectors.zendesk import ZendeskConnector
from src.ai.llm_client import OllamaClient
from src.services.processor import TicketProcessor
from src.core.logger import setup_logging

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self) -> None:
        setup_logging()
        self._settings = get_settings()
        self._llm = OllamaClient()
        self._processor = TicketProcessor(self._llm)
        self._connectors: list[ITSMConnector] = []

    def _init_connectors(self) -> None:
        s = self._settings
        if s.freshservice_domain:
            self._connectors.append(FreshserviceConnector())
            logger.info("Freshservice connector initialized")
        if s.zendesk_domain:
            self._connectors.append(ZendeskConnector())
            logger.info("Zendesk connector initialized")

    async def run_once(self, max_tickets: int = 20) -> int:
        self._init_connectors()
        if not self._connectors:
            logger.warning("No ITSM connectors configured")
            return 0

        processed = 0
        for connector in self._connectors:
            tickets = await connector.list_tickets(status="open", limit=max_tickets)
            for ticket in tickets:
                try:
                    result = await self._processor.process(ticket)
                    logger.info("Processed ticket %s: requires_escalation=%s", ticket.id, result["requires_escalation"])
                    if result["requires_escalation"]:
                        await connector.add_note(
                            ticket.id,
                            f"[AI] Clasificacion: {result['classification']}\n"
                            f"Sugerencia: {result['resolution_suggestion']}\n"
                            "Requiere revision manual.",
                            public=False,
                        )
                    else:
                        await connector.add_note(
                            ticket.id,
                            f"[AI] Resolucion sugerida aplicada automaticamente.\n"
                            f"{result['resolution_suggestion']}",
                            public=True,
                        )
                    processed += 1
                except Exception:
                    logger.exception("Failed to process ticket %s", ticket.id)
        return processed

    async def run_loop(self, interval_secs: int = 60, max_tickets: int = 20) -> None:
        logger.info("Starting orchestrator loop (interval=%ss)", interval_secs)
        while True:
            try:
                count = await self.run_once(max_tickets)
                logger.info("Cycle complete — processed %s tickets", count)
            except Exception:
                logger.exception("Cycle failed")
            await asyncio.sleep(interval_secs)

    async def shutdown(self) -> None:
        for c in self._connectors:
            if hasattr(c, "close"):
                await c.close()
        logger.info("Orchestrator shut down")


async def main_async() -> None:
    orch = Orchestrator()
    try:
        await orch.run_loop()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        await orch.shutdown()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
