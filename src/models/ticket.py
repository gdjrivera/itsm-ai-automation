from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TicketStatus(StrEnum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(StrEnum):
    INCIDENT = "incident"
    SERVICE_REQUEST = "service_request"
    CHANGE = "change"
    PROBLEM = "problem"


class Ticket(BaseModel):
    id: str
    external_id: str | None = None
    title: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory = TicketCategory.INCIDENT
    assignee: str | None = None
    requester: str | None = None
    department: str | None = None
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source: str = ""

    @property
    def is_actionable(self) -> bool:
        return self.status in (TicketStatus.OPEN, TicketStatus.PENDING)

    def summary(self, max_len: int = 200) -> str:
        desc = self.description[:max_len].replace("\n", " ")
        if len(self.description) > max_len:
            desc += "..."
        return f"[{self.source}] #{self.id} ({self.priority}) {self.title}: {desc}"
