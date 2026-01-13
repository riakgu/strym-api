import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware.
    Limits requests per IP address.
    """
    
    RATE_LIMIT = 100  # requests
    WINDOW = 60  # seconds
    PREFIX = "strym:ratelimit:"
    
    def __init__(self, app, redis_client: redis.Redis | None = None):
        super().__init__(app)
        self._redis = redis_client
    
    async def init(self) -> None:
        """Initialize Redis connection."""
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url)
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Skip if Redis not available
        if not self._redis:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        key = f"{self.PREFIX}{client_ip}"
        
        try:
            # Get current count
            current = await self._redis.get(key)
            
            if current is None:
                # First request - set counter with TTL
                await self._redis.setex(key, self.WINDOW, 1)
                remaining = self.RATE_LIMIT - 1
            else:
                count = int(current)
                if count >= self.RATE_LIMIT:
                    # Rate limit exceeded
                    ttl = await self._redis.ttl(key)
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "message": "Rate limit exceeded",
                                "type": "RateLimitError",
                                "retry_after": ttl,
                            }
                        },
                        headers={
                            "X-RateLimit-Limit": str(self.RATE_LIMIT),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(time.time()) + ttl),
                            "Retry-After": str(ttl),
                        }
                    )
                
                # Increment counter
                await self._redis.incr(key)
                remaining = self.RATE_LIMIT - count - 1
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            
            return response
            
        except Exception:
            # If Redis fails, allow request
            return await call_next(request)
