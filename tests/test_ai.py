import pytest

from src.ai.llm_client import OllamaClient
from src.ai.prompts import classify_ticket_prompt, suggest_resolution_prompt


@pytest.mark.asyncio
async def test_ollama_unavailable() -> None:
    client = OllamaClient()
    available = await client.is_available()
    # Without Ollama running, this should be False
    assert available is False


def test_classify_prompt_contains_title() -> None:
    prompt = classify_ticket_prompt("Login fails", "User cannot log in")
    assert "Login fails" in prompt
    assert "User cannot log in" in prompt


def test_resolution_prompt_contains_summary() -> None:
    prompt = suggest_resolution_prompt("Ticket summary here")
    assert "Ticket summary here" in prompt
