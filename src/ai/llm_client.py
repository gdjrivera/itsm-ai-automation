import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    content: str
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class OllamaClient:
    def __init__(self) -> None:
        s = get_settings()
        self._base = s.ollama_base_url.rstrip("/")
        self._model = s.ollama_model
        self._timeout = s.ollama_timeout

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        structured: type | None = None,
    ) -> LLMResult:
        import httpx

        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(base_url=self._base, timeout=self._timeout) as c:
            r = await c.post("/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()

        content = data.get("response", "")
        if structured:
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                logger.warning("LLM output is not valid JSON, returning raw")

        return LLMResult(
            content=content,
            model=data.get("model", self._model),
            tokens_input=data.get("prompt_eval_count", 0),
            tokens_output=data.get("eval_count", 0),
        )

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        import httpx

        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(base_url=self._base, timeout=self._timeout) as c:
            async with c.stream("POST", "/api/generate", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if chunk.get("done"):
                            break
                        token = chunk.get("response", "")
                        if token:
                            yield token
                    except json.JSONDecodeError:
                        continue

    async def is_available(self) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(base_url=self._base, timeout=5) as c:
                r = await c.get("/api/tags")
                return r.is_success
        except Exception:
            return False
