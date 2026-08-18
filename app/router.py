import os

from app.config import ROUTING_TABLE
from app.adapters import OpenAIAdapter, AnthropicAdapter, GroqAdapter

ADAPTER_CLASSES = {
    "OpenAIAdapter": OpenAIAdapter,
    "AnthropicAdapter": AnthropicAdapter,
    "GroqAdapter": GroqAdapter,
}


class RoutingError(Exception):
    pass


def resolve_provider(model_string: str):
    """
    model_string looks like "anthropic/claude-sonnet-4-6" or "openai/gpt-4o-mini".
    Returns (adapter_instance, model_id).

    This is the entire "routing" decision - split on '/', look up the
    provider's config, instantiate its adapter with the gateway's own
    provider API key. No ML, just a dict lookup.
    """
    if "/" not in model_string:
        raise RoutingError(f"Model string '{model_string}' must be in 'provider/model' format")

    provider_name, model_id = model_string.split("/", 1)
    config = ROUTING_TABLE.get(provider_name)
    if config is None:
        raise RoutingError(f"Unknown provider '{provider_name}'")

    api_key = os.getenv(config.api_key_env)
    if not api_key:
        raise RoutingError(f"Missing API key: set {config.api_key_env} in your environment")

    adapter_cls = ADAPTER_CLASSES[config.adapter]
    adapter = adapter_cls(config.base_url, api_key)
    return adapter, model_id
