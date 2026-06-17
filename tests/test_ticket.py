from datetime import datetime

from src.models.ticket import Ticket, TicketStatus, TicketPriority


def test_ticket_creation() -> None:
    t = Ticket(
        id="1",
        title="Test ticket",
        description="Something is broken",
        source="freshservice",
    )
    assert t.status == TicketStatus.OPEN
    assert t.priority == TicketPriority.MEDIUM
    assert t.is_actionable is True


def test_ticket_not_actionable_when_closed() -> None:
    t = Ticket(
        id="2",
        title="Closed ticket",
        description="Done",
        status=TicketStatus.CLOSED,
        source="freshservice",
    )
    assert t.is_actionable is False


def test_ticket_summary() -> None:
    t = Ticket(id="3", title="Login error", description="Cannot log in", source="zendesk")
    summary = t.summary()
    assert "[zendesk] #3 (medium) Login error: Cannot log in" in summary


def test_ticket_summary_truncates() -> None:
    long_desc = "A" * 500
    t = Ticket(id="4", title="Long", description=long_desc, source="test")
    summary = t.summary(max_len=50)
    assert summary.endswith("...")
    assert len(summary) < 300
