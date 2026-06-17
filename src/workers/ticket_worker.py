import logging

import redis
from rq import Queue, Worker
from rq.job import Job

from src.config.settings import get_settings
from src.core.logger import setup_logging

logger = logging.getLogger(__name__)


def process_ticket_job(ticket_id: str, source: str) -> dict:
    setup_logging()
    from src.ai.llm_client import OllamaClient
    from src.services.processor import TicketProcessor

    llm = OllamaClient()
    processor = TicketProcessor(llm)
    import asyncio

    async def _run():
        from src.connectors.freshservice import FreshserviceConnector
        from src.connectors.zendesk import ZendeskConnector

        if source == "freshservice":
            conn = FreshserviceConnector()
        elif source == "zendesk":
            conn = ZendeskConnector()
        else:
            raise ValueError(f"Unknown source: {source}")

        try:
            ticket = await conn.get_ticket(ticket_id)
            if not ticket:
                return {"error": "Ticket not found"}
            result = await processor.process(ticket)
            await conn.add_note(ticket.id, f"[AI Worker] Procesado: {result}", public=False)
            return result
        finally:
            await conn.close()

    return asyncio.run(_run())


def main() -> None:
    setup_logging()
    settings = get_settings()

    conn = redis.from_url(settings.redis_url)
    queue = Queue(settings.worker_queue, connection=conn)
    worker = Worker([queue], connection=conn)
    logger.info("RQ Worker started — queue: %s", settings.worker_queue)
    worker.work()


if __name__ == "__main__":
    main()
