import pytest

from src.connectors.freshservice import FreshserviceConnector
from src.connectors.zendesk import ZendeskConnector


@pytest.mark.asyncio
async def test_freshservice_health_returns_false_without_config() -> None:
    connector = FreshserviceConnector()
    try:
        healthy = await connector.health_check()
        assert healthy is False
    finally:
        await connector.close()


@pytest.mark.asyncio
async def test_zendesk_health_returns_false_without_config() -> None:
    connector = ZendeskConnector()
    try:
        healthy = await connector.health_check()
        assert healthy is False
    finally:
        await connector.close()
