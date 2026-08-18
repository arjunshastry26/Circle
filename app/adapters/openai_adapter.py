import json
from typing import AsyncIterator, Tuple

import httpx

from .base import ProviderAdapter


class ProviderError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class OpenAIAdapter(ProviderAdapter):
    """
    OpenAI's API shape IS the unified schema this gateway standardizes on,
    so this adapter is close to a passthrough. Any OpenAI-compatible
    provider (Groq, Together, etc.) can reuse this class directly - see
    groq_adapter.py.
    """

    def build_request(self, unified_request: dict, model_id: str) -> Tuple[str, dict, dict]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model_id,
            "messages": unified_request["messages"],
            "temperature": unified_request.get("temperature", 1.0),
            "max_tokens": unified_request.get("max_tokens"),
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        body = {k: v for k, v in body.items() if v is not None}
        return url, headers, body

    async def stream(self, unified_request: dict, model_id: str) -> AsyncIterator[dict]:
        url, headers, body = self.build_request(unified_request, model_id)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise ProviderError(resp.status_code, error_body.decode())

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload.strip() == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    # Already unified shape - pass through as-is.
                    yield chunk
