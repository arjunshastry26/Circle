from fastapi import Header, HTTPException
from app.config import GATEWAY_API_KEYS


async def verify_api_key(authorization: str = Header(default=None)) -> str:
    """
    Expects 'Authorization: Bearer <key>'.

    This checks the key against GATEWAY_API_KEYS - keys clients use to call
    YOUR gateway. It has nothing to do with provider API keys; those live
    only in the gateway's own environment and clients never see them.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    key = authorization[len("Bearer "):].strip()
    if key not in GATEWAY_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return key
