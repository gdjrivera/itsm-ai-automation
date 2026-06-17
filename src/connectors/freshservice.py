from collections.abc import AsyncIterator
from datetime import datetime

import httpx

from src.config.settings import get_settings
from src.connectors.base import ITSMConnector, TicketList
from src.models.ticket import Ticket, TicketPriority, TicketStatus

STATUS_MAP: dict[int, TicketStatus] = {
    2: TicketStatus.OPEN,
    3: TicketStatus.PENDING,
    4: TicketStatus.PENDING,
    5: TicketStatus.RESOLVED,
    6: TicketStatus.CLOSED,
}

PRIORITY_MAP: dict[int, TicketPriority] = {
    1: TicketPriority.LOW,
    2: TicketPriority.MEDIUM,
    3: TicketPriority.HIGH,
    4: TicketPriority.URGENT,
}

_REVERSE_STATUS = {v: k for k, v in STATUS_MAP.items()}
_REVERSE_PRIORITY = {v: k for k, v in PRIORITY_MAP.items()}


class FreshserviceConnector(ITSMConnector):
    def __init__(self) -> None:
        s = get_settings()
        self._base = s.freshservice_base_url
        self._api_key = s.freshservice_api_key.get_secret_value()
        self._page_size = s.freshservice_page_size
        self._client = httpx.AsyncClient(
            base_url=self._base,
            auth=httpx.BasicAuth(self._api_key, "X"),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            r = await self._client.get("/api/v2/tickets", params={"per_page": 1})
            return r.is_success
        except Exception:
            return False

    async def get_ticket(self, ticket_id: str) -> Ticket | None:
        r = await self._client.get(f"/api/v2/tickets/{ticket_id}")
        if not r.is_success:
            return None
        data = r.json()["ticket"]
        return self._parse(data)

    async def list_tickets(
        self, status: str | None = None, priority: str | None = None, limit: int = 50
    ) -> TicketList:
        params: dict = {"per_page": min(limit, self._page_size)}
        filters = []
        if status and status in _REVERSE_STATUS:
            filters.append(f"status:{_REVERSE_STATUS[status]}")
        if priority and priority in _REVERSE_PRIORITY:
            filters.append(f"urgency:{_REVERSE_PRIORITY[priority]}")
        if filters:
            params["query"] = " AND ".join(filters)
        r = await self._client.get("/api/v2/tickets", params=params)
        if not r.is_success:
            return []
        return [self._parse(t) for t in r.json().get("tickets", [])]

    async def stream_all(self, batch_size: int = 50) -> AsyncIterator[TicketList]:
        page = 1
        while True:
            r = await self._client.get(
                "/api/v2/tickets",
                params={"per_page": min(batch_size, self._page_size), "page": page},
            )
            if not r.is_success:
                break
            tickets = r.json().get("tickets", [])
            if not tickets:
                break
            yield [self._parse(t) for t in tickets]
            page += 1

    async def update_ticket(self, ticket_id: str, fields: dict) -> Ticket | None:
        payload: dict = {}
        if "status" in fields:
            payload["status"] = _REVERSE_STATUS.get(fields["status"])
        if "priority" in fields:
            payload["urgency"] = _REVERSE_PRIORITY.get(fields["priority"])
        if "assignee" in fields:
            payload["responder_id"] = fields["assignee"]
        if "tags" in fields:
            payload["tags"] = fields["tags"]
        r = await self._client.put(f"/api/v2/tickets/{ticket_id}", json={"ticket": payload})
        if not r.is_success:
            return None
        return self._parse(r.json()["ticket"])

    async def add_note(self, ticket_id: str, body: str, public: bool = True) -> bool:
        r = await self._client.post(
            f"/api/v2/tickets/{ticket_id}/notes",
            json={"note": {"body": body, "private": not public}},
        )
        return r.is_success

    def _parse(self, data: dict) -> Ticket:
        return Ticket(
            id=str(data["id"]),
            title=data.get("subject", ""),
            description=data.get("description", ""),
            status=STATUS_MAP.get(data.get("status"), TicketStatus.OPEN),
            priority=PRIORITY_MAP.get(data.get("urgency"), TicketPriority.MEDIUM),
            assignee=str(data.get("responder_id", "")) or None,
            requester=str(data.get("requester_id", "")) or None,
            department=str(data.get("department_id", "")) or None,
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            created_at=self._parse_dt(data.get("created_at")),
            updated_at=self._parse_dt(data.get("updated_at")),
            source="freshservice",
        )

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
