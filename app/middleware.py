import time
import logging
from datetime import datetime, timezone
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.config import get_settings

# Configure logger
logger = logging.getLogger("strym.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests.
    Logs: method, path, status, duration, client IP
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        # Log request
        log_message = (
            f"{request.method} {request.url.path} "
            f"{response.status_code} {duration_ms}ms {client_ip}"
        )
        
        # Use appropriate log level based on status
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Also print to console for development
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {log_message}")
        
        return response


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
