"""
Cache management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.utils.cache import get_intent_cache, get_llm_response_cache
from app.utils.vectorstore import get_vector_store
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

    # Get vector store stats
    try:
        vector_store = get_vector_store()
        vector_store_stats = {
            "loaded": True,
            "faiss_vectors": vector_store.faiss_store.index.ntotal
            if vector_store.faiss_store
            else 0,
            "bm25_documents": len(vector_store.documents),
            "doc_id_mappings": len(vector_store.doc_id_map),
        }
    except Exception as e:
        vector_store_stats = {"loaded": False, "error": str(e)}

    return {
        "enabled": settings.ENABLE_CACHE,
        "intent_cache": intent_cache.get_stats(),
        "llm_response_cache": llm_cache.get_stats(),
        "vector_store_cache": vector_store_stats,
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
        "INTENT_CACHE_TTL_HOURS": settings.INTENT_CACHE_TTL / 3600,
        "LLM_RESPONSE_CACHE_TTL": settings.LLM_RESPONSE_CACHE_TTL,
        "LLM_RESPONSE_CACHE_TTL_HOURS": settings.LLM_RESPONSE_CACHE_TTL / 3600,
        "LLM_RESPONSE_CACHE_MAX_SIZE": settings.LLM_RESPONSE_CACHE_MAX_SIZE,
    }


@router.post("/clear/vectorstore")
async def reload_vector_store() -> Dict[str, str]:
    """Reload vector store from disk (FAISS + BM25)"""
    from app.utils.vectorstore import rebuild_vector_store

    rebuild_vector_store()
    return {
        "status": "ok",
        "message": "Vector store reset, will reload from disk on next access",
    }


@router.post("/rebuild/vectorstore")
async def rebuild_vector_store_from_db(db: AsyncSession = Depends(get_db)):
    """Rebuild vector store from database documents (re-index all)"""
    from app.utils.vectorstore import rebuild_vector_store_from_db as rebuild_fn

    try:
        await rebuild_fn(db)
        return {"status": "ok", "message": "Vector store rebuilt from database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")
