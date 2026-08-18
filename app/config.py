import os
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    base_url: str
    api_key_env: str
    adapter: str  # adapter class name, resolved in router.py


# The whole "which provider handles this model" decision lives here.
# Add a provider by adding one entry + one adapter file - nothing else changes.
ROUTING_TABLE = {
    "openai": ProviderConfig(
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        adapter="OpenAIAdapter",
    ),
    "anthropic": ProviderConfig(
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        adapter="AnthropicAdapter",
    ),
    "groq": ProviderConfig(
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        adapter="GroqAdapter",
    ),
}

# Crude per-1M-token pricing (USD) for the usage ledger demo.
# Update these to match current provider pricing pages.
PRICING = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "groq/llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
}

# Keys that are allowed to call THIS gateway (not provider keys).
GATEWAY_API_KEYS = set(
    k.strip() for k in os.getenv("GATEWAY_API_KEYS", "test-key-123").split(",") if k.strip()
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://openrouter:openrouter@localhost:5432/openrouter")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
