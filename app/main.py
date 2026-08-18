import json
import logging

from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from app.auth import verify_api_key
from app.rate_limit import check_rate_limit
from app.router import resolve_provider, RoutingError
from app.ledger import log_usage
from app.adapters import ProviderError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="OpenRouter Clone")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, api_key: str = Depends(verify_api_key)):
    await check_rate_limit(api_key)

    body = await request.json()
    model_string = body.get("model")
    if not model_string:
        return JSONResponse(status_code=400, content={"error": "Missing 'model' field"})

    try:
        adapter, model_id = resolve_provider(model_string)
    except RoutingError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    async def event_stream():
        prompt_tokens = 0
        completion_tokens = 0
        try:
            async for chunk in adapter.stream(body, model_id):
                usage = chunk.get("usage")
                if usage:
                    prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                    completion_tokens = usage.get("completion_tokens", completion_tokens)
                yield f"data: {json.dumps(chunk)}\n\n"
        except ProviderError as e:
            logger.error(f"Provider error: {e}")
            yield f"data: {json.dumps({'error': {'message': e.message, 'code': e.status_code}})}\n\n"
        else:
            if prompt_tokens or completion_tokens:
                try:
                    await log_usage(api_key, model_string, prompt_tokens, completion_tokens)
                except Exception as e:
                    logger.error(f"Failed to log usage: {e}")
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
