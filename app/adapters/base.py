from abc import ABC, abstractmethod
from typing import AsyncIterator, Tuple


class ProviderAdapter(ABC):
    """
    Every provider adapter implements the same two-way contract:

      - build_request(): translate the unified request into this
        provider's own shape (fields, auth header, endpoint path).

      - stream(): call the provider and yield chunks already normalized
        back into the unified, OpenAI-compatible streaming format:
            {"choices": [{"delta": {"content": "..."}, "finish_reason": None}]}
        with a final chunk carrying usage info:
            {"choices": [...], "usage": {"prompt_tokens": N, "completion_tokens": N}}

    Everything upstream of the adapter (router, gateway, ledger) only ever
    speaks this one shape. Only the adapter needs to know the provider's
    dialect, in both directions.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    @abstractmethod
    def build_request(self, unified_request: dict, model_id: str) -> Tuple[str, dict, dict]:
        """Return (url, headers, json_body) for this provider's API."""
        raise NotImplementedError

    @abstractmethod
    async def stream(self, unified_request: dict, model_id: str) -> AsyncIterator[dict]:
        raise NotImplementedError
        yield  # pragma: no cover - keeps this an async generator for subclasses
