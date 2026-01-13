from typing import Annotated

from fastapi import Header, HTTPException, Query

from app.config import get_settings


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None
) -> str:
    """
    Verify API key from X-API-Key header.
    Returns the validated API key.
    """
    settings = get_settings()
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Missing API key",
                    "type": "AuthenticationError",
                }
            }
        )
    
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Invalid API key",
                    "type": "AuthenticationError",
                }
            }
        )
    
    return x_api_key


async def verify_api_key_websocket(
    api_key: Annotated[str | None, Query()] = None
) -> str:
    """
    Verify API key from query parameter for WebSocket.
    Usage: ws://localhost:3000/stream?api_key=xxx
    """
    settings = get_settings()
    
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Invalid or missing API key",
                    "type": "AuthenticationError",
                }
            }
        )
    
    return api_key


# Type aliases for dependencies
ApiKeyDep = Annotated[str, verify_api_key]
ApiKeyWsDep = Annotated[str, verify_api_key_websocket]
