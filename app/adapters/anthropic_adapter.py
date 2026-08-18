import json
from typing import AsyncIterator, Tuple

import httpx

from .base import ProviderAdapter
from .openai_adapter import ProviderError


class AnthropicAdapter(ProviderAdapter):
    """
    Anthropic's shape differs from the unified schema in two ways that
    matter:

      1. Request: the system prompt is a top-level `system` field, not a
         message with role="system" mixed into the messages list.

      2. Streaming: events are type-tagged envelopes (message_start,
         content_block_delta, message_delta, message_stop) instead of
         OpenAI's flat delta chunks, and usage arrives split across two
         different event types instead of one final chunk.

    This adapter absorbs both differences so nothing upstream has to know
    Anthropic's format exists.
    """

    def build_request(self, unified_request: dict, model_id: str) -> Tuple[str, dict, dict]:
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        messages = unified_request["messages"]
        system_prompt = None
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})

        body = {
            "model": model_id,
            "messages": chat_messages,
            "max_tokens": unified_request.get("max_tokens") or 1024,
            "temperature": unified_request.get("temperature", 1.0),
            "stream": True,
        }
        if system_prompt:
            body["system"] = system_prompt
        return url, headers, body

    async def stream(self, unified_request: dict, model_id: str) -> AsyncIterator[dict]:
        url, headers, body = self.build_request(unified_request, model_id)
        input_tokens = 0
        output_tokens = 0

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise ProviderError(resp.status_code, error_body.decode())

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    event = json.loads(line[len("data: "):])
                    etype = event.get("type")

                    if etype == "message_start":
                        input_tokens = event["message"]["usage"].get("input_tokens", 0)

                    elif etype == "content_block_delta":
                        delta = event["delta"]
                        if delta.get("type") == "text_delta":
                            yield {
                                "choices": [{"delta": {"content": delta["text"]}, "finish_reason": None}]
                            }

                    elif etype == "message_delta":
                        output_tokens = event.get("usage", {}).get("output_tokens", output_tokens)

                    elif etype == "message_stop":
                        yield {
                            "choices": [{"delta": {}, "finish_reason": "stop"}],
                            "usage": {
                                "prompt_tokens": input_tokens,
                                "completion_tokens": output_tokens,
                                "total_tokens": input_tokens + output_tokens,
                            },
                        }
