from collections.abc import AsyncIterator
from datetime import datetime

import httpx

from src.config.settings import get_settings
from src.connectors.base import ITSMConnector, TicketList
from src.models.ticket import Ticket, TicketPriority, TicketStatus

STATUS_MAP: dict[str, TicketStatus] = {
    "new": TicketStatus.OPEN,
    "open": TicketStatus.OPEN,
    "pending": TicketStatus.PENDING,
    "hold": TicketStatus.PENDING,
    "solved": TicketStatus.RESOLVED,
    "closed": TicketStatus.CLOSED,
}

PRIORITY_MAP: dict[str, TicketPriority] = {
    "low": TicketPriority.LOW,
    "normal": TicketPriority.MEDIUM,
    "high": TicketPriority.HIGH,
    "urgent": TicketPriority.URGENT,
}


class ZendeskConnector(ITSMConnector):
    def __init__(self) -> None:
        s = get_settings()
        self._base = s.zendesk_base_url
        self._email = s.zendesk_email
        self._token = s.zendesk_api_token.get_secret_value()
        self._page_size = s.zendesk_page_size
        self._client = httpx.AsyncClient(
            base_url=self._base,
            auth=httpx.BasicAuth(f"{self._email}/token", self._token),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            r = await self._client.get("/api/v2/tickets.json", params={"per_page": 1})
            return r.is_success
        except Exception:
            return False

    async def get_ticket(self, ticket_id: str) -> Ticket | None:
        r = await self._client.get(f"/api/v2/tickets/{ticket_id}.json")
        if not r.is_success:
            return None
        return self._parse(r.json()["ticket"])

    async def list_tickets(
        self, status: str | None = None, priority: str | None = None, limit: int = 50
    ) -> TicketList:
        params: dict = {"per_page": min(limit, self._page_size)}
        r = await self._client.get("/api/v2/tickets.json", params=params)
        if not r.is_success:
            return []
        return [self._parse(t) for t in r.json().get("tickets", [])]

    async def stream_all(self, batch_size: int = 50) -> AsyncIterator[TicketList]:
        url: str | None = "/api/v2/tickets.json"
        while url:
            r = await self._client.get(url, params={"per_page": min(batch_size, self._page_size)})
            if not r.is_success:
                break
            body = r.json()
            tickets = body.get("tickets", [])
            if not tickets:
                break
            yield [self._parse(t) for t in tickets]
            url = body.get("next_page")

    async def update_ticket(self, ticket_id: str, fields: dict) -> Ticket | None:
        payload: dict = {}
        if "status" in fields:
            payload["status"] = fields["status"]
        if "priority" in fields:
            payload["priority"] = fields["priority"]
        if "assignee" in fields:
            payload["assignee_id"] = int(fields["assignee"])
        if "tags" in fields:
            payload["tags"] = fields["tags"]
        r = await self._client.put(
            f"/api/v2/tickets/{ticket_id}.json", json={"ticket": payload}
        )
        if not r.is_success:
            return None
        return self._parse(r.json()["ticket"])

    async def add_note(self, ticket_id: str, body: str, public: bool = True) -> bool:
        r = await self._client.post(
            f"/api/v2/tickets/{ticket_id}/comments.json",
            json={"ticket": {"comment": {"body": body, "public": public}}},
        )
        return r.is_success

    def _parse(self, data: dict) -> Ticket:
        return Ticket(
            id=str(data["id"]),
            title=data.get("subject", ""),
            description=data.get("description", ""),
            status=STATUS_MAP.get(data.get("status", ""), TicketStatus.OPEN),
            priority=PRIORITY_MAP.get(data.get("priority", ""), TicketPriority.MEDIUM),
            assignee=str(data.get("assignee_id", "")) or None,
            requester=str(data.get("requester_id", "")) or None,
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            created_at=self._parse_dt(data.get("created_at")),
            updated_at=self._parse_dt(data.get("updated_at")),
            source="zendesk",
        )

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
