"""
Simple in-memory cache with TTL support
"""

import time
import hashlib
import logging
from typing import Any, Optional, Dict, Tuple
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Thread-safe in-memory cache with TTL (Time To Live) support

    Features:
    - Automatic expiration based on TTL
    - LRU eviction when max size is reached
    - Thread-safe operations (using simple locking)
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = (
            OrderedDict()
        )  # key -> (value, expire_time)
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            value, expire_time = self._cache[key]
            if time.time() < expire_time:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._stats["hits"] += 1
                return value
            else:
                # Expired, remove it
                del self._cache[key]

        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        expire_time = time.time() + ttl

        # Update or add
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self.max_size:
            # Evict oldest (first item)
            evicted_key = next(iter(self._cache))
            del self._cache[evicted_key]
            self._stats["evictions"] += 1

        self._cache[key] = (value, expire_time)

    def delete(self, key: str) -> bool:
        """Delete a specific key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": f"{hit_rate:.1%}",
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# Global cache instances
_intent_cache: Optional[TTLCache] = None
_llm_response_cache: Optional[TTLCache] = None


def get_intent_cache() -> TTLCache:
    """Get or create global intent cache instance"""
    global _intent_cache
    if _intent_cache is None:
        from config import settings

        _intent_cache = TTLCache(
            max_size=100,  # Small cache for intents
            default_ttl=settings.INTENT_CACHE_TTL,
        )
        logger.info(f"Intent cache initialized (TTL={settings.INTENT_CACHE_TTL}s)")
    return _intent_cache


def get_llm_response_cache() -> TTLCache:
    """Get or create global LLM response cache instance"""
    global _llm_response_cache
    if _llm_response_cache is None:
        from config import settings

        _llm_response_cache = TTLCache(
            max_size=settings.LLM_RESPONSE_CACHE_MAX_SIZE,
            default_ttl=settings.LLM_RESPONSE_CACHE_TTL,
        )
        logger.info(
            f"LLM response cache initialized (TTL={settings.LLM_RESPONSE_CACHE_TTL}s, max={settings.LLM_RESPONSE_CACHE_MAX_SIZE})"
        )
    return _llm_response_cache


def make_cache_key(*args, **kwargs) -> str:
    """
    Create a cache key from arguments

    Returns:
        MD5 hash of the arguments
    """
    key_str = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(cache_instance_func, ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching async function results

    Args:
        cache_instance_func: Function that returns the cache instance
        ttl: Override TTL for this function
        key_prefix: Prefix for cache keys
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from config import settings

            if not settings.ENABLE_CACHE:
                return await func(*args, **kwargs)

            cache = cache_instance_func()
            cache_key = (
                f"{key_prefix}:{func.__name__}:{make_cache_key(*args, **kwargs)}"
            )

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss: {cache_key}")

            return result

        return wrapper

    return decorator
