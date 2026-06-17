from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from src.models.ticket import Ticket

TicketList = list[Ticket]


class ITSMConnector(ABC):
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> Ticket | None: ...

    @abstractmethod
    async def list_tickets(
        self,
        status: str | None = None,
        priority: str | None = None,
        limit: int = 50,
    ) -> TicketList: ...

    @abstractmethod
    async def stream_all(self, batch_size: int = 50) -> AsyncIterator[TicketList]: ...

    @abstractmethod
    async def update_ticket(
        self, ticket_id: str, fields: dict
    ) -> Ticket | None: ...

    @abstractmethod
    async def add_note(self, ticket_id: str, body: str, public: bool = True) -> bool: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
