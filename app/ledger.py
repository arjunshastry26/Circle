from app.db import get_pool
from app.config import PRICING


def estimate_cost(model_string: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = PRICING.get(model_string)
    if not rates:
        return 0.0
    return (prompt_tokens / 1_000_000) * rates["input"] + (completion_tokens / 1_000_000) * rates["output"]


async def log_usage(api_key: str, model_string: str, prompt_tokens: int, completion_tokens: int) -> float:
    cost = estimate_cost(model_string, prompt_tokens, completion_tokens)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO usage_log (api_key, model, prompt_tokens, completion_tokens, cost_usd, created_at)
            VALUES ($1, $2, $3, $4, $5, now())
            """,
            api_key, model_string, prompt_tokens, completion_tokens, cost,
        )
    return cost
