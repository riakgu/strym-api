import json
import hashlib
from typing import Any

import redis.asyncio as redis

from app.config import get_settings


class CacheService:
    """Redis-based caching service."""
    
    PREFIX = "strym:cache:"
    DEFAULT_TTL = 60  # seconds
    
    def __init__(self):
        self._redis: redis.Redis | None = None
    
    async def init(self) -> None:
        """Initialize Redis connection."""
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url)
        print("Cache service initialized")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
        print("Cache service closed")
    
    def _make_key(self, prefix: str, params: dict) -> str:
        """Generate cache key from parameters."""
        # Sort params for consistent key
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        hash_val = hashlib.md5(sorted_params.encode()).hexdigest()[:16]
        return f"{self.PREFIX}{prefix}:{hash_val}"
    
    async def get(self, prefix: str, params: dict) -> Any | None:
        """Get cached value."""
        if not self._redis:
            return None
        
        key = self._make_key(prefix, params)
        data = await self._redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def set(
        self, 
        prefix: str, 
        params: dict, 
        value: Any, 
        ttl: int | None = None
    ) -> None:
        """Set cached value."""
        if not self._redis:
            return
        
        key = self._make_key(prefix, params)
        data = json.dumps(value, default=str)
        await self._redis.setex(key, ttl or self.DEFAULT_TTL, data)
    
    async def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all cache entries with prefix."""
        if not self._redis:
            return 0
        
        pattern = f"{self.PREFIX}{prefix}:*"
        keys = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self._redis.delete(*keys)
        
        return len(keys)


# Global instance
cache_service = CacheService()
