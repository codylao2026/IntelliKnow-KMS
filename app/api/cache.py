"""
Cache management API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.utils.cache import get_intent_cache, get_llm_response_cache
from config import settings

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics

    Returns statistics for all cache instances including hit rate, size, etc.
    """
    intent_cache = get_intent_cache()
    llm_cache = get_llm_response_cache()

    return {
        "enabled": settings.ENABLE_CACHE,
        "intent_cache": intent_cache.get_stats(),
        "llm_response_cache": llm_cache.get_stats(),
    }


@router.post("/clear")
async def clear_all_caches() -> Dict[str, str]:
    """
    Clear all caches

    Clears both intent and LLM response caches.
    """
    intent_cache = get_intent_cache()
    llm_cache = get_llm_response_cache()

    intent_cache.clear()
    llm_cache.clear()

    return {"status": "ok", "message": "All caches cleared"}


@router.post("/clear/intent")
async def clear_intent_cache() -> Dict[str, str]:
    """Clear intent cache only"""
    intent_cache = get_intent_cache()
    intent_cache.clear()
    return {"status": "ok", "message": "Intent cache cleared"}


@router.post("/clear/llm")
async def clear_llm_cache() -> Dict[str, str]:
    """Clear LLM response cache only"""
    llm_cache = get_llm_response_cache()
    llm_cache.clear()
    return {"status": "ok", "message": "LLM response cache cleared"}


@router.get("/config")
async def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration"""
    return {
        "ENABLE_CACHE": settings.ENABLE_CACHE,
        "INTENT_CACHE_TTL": settings.INTENT_CACHE_TTL,
        "LLM_RESPONSE_CACHE_TTL": settings.LLM_RESPONSE_CACHE_TTL,
        "LLM_RESPONSE_CACHE_MAX_SIZE": settings.LLM_RESPONSE_CACHE_MAX_SIZE,
    }
