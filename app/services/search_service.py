"""
Search service - Hybrid Search implementation with Rerank
"""
import os
import logging
from typing import List, Dict, Any, Optional

from app.utils.vectorstore import get_vector_store
from config import settings

logger = logging.getLogger(__name__)


async def search_documents(
    query: str,
    intent_id: Optional[int] = None,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Search documents using hybrid search (FAISS + BM25 with RRF)

    Args:
        query: Search query
        intent_id: Filter by intent ID
        top_k: Number of results

    Returns:
        List of search results with content and scores
    """
    if top_k is None:
        top_k = settings.TOP_K_DOCUMENTS

    try:
        vector_store = get_vector_store()
        results = vector_store.search(
            query=query,
            intent_id=intent_id,
            top_k=top_k
        )

        # Filter by intent_id if specified
        if intent_id is not None:
            results = [r for r in results if r.get("intent_id") == intent_id]

        logger.info(f"Search for '{query}' returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


async def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Rerank search results using BGE-Reranker-v2-M3 model

    Args:
        query: Original query
        results: Search results
        top_k: Number of results to return

    Returns:
        Reranked results
    """
    if top_k is None:
        top_k = settings.RERANK_TOP_K

    if not results:
        return []

    # Get documents for reranking
    documents = [r.get("content", "") for r in results]
    
    try:
        # Use SiliconFlow rerank API
        api_key = os.getenv("SILICONCLOUD_API_KEY", "")
        if not api_key:
            logger.warning("No SILICONCLOUD_API_KEY, skipping rerank")
            return results[:top_k]

        import httpx
        
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.post(
                "https://api.siliconflow.cn/v1/rerank",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.RERANK_MODEL,
                    "query": query,
                    "documents": documents,
                    "top_n": top_k
                },
                timeout=30.0
            )

            if response.status_code == 200:
                rerank_data = response.json()
                reranked = rerank_data.get("results", [])
                
                # Map reranked results back to original format
                reranked_results = []
                for item in reranked:
                    idx = item.get("index", 0)
                    if idx < len(results):
                        result = results[idx].copy()
                        result["rerank_score"] = item.get("relevance_score", 0)
                        result["score"] = item.get("relevance_score", 0)
                        reranked_results.append(result)
                
                logger.info(f"Reranked {len(results)} results to {len(reranked_results)} using {settings.RERANK_MODEL}")
                return reranked_results
            else:
                logger.warning(f"Rerank API error: {response.status_code} - {response.text}")
                return results[:top_k]

    except Exception as e:
        logger.warning(f"Rerank failed: {e}")
        return results[:top_k]


async def rewrite_query(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Rewrite query using LLM for better search results.
    Only rewrites when query is short (< 5 words) and has conversation history.

    Args:
        query: Original query
        conversation_history: Previous conversation (last 3 turns)

    Returns:
        Rewritten query or original if conditions not met
    """
    # Only rewrite short queries with history
    word_count = len(query.split())
    if word_count >= 5 or not conversation_history:
        return query

    # Build context from last 3 turns
    history_text = "\n".join([
        f"Turn {i+1}:\nUser: {msg.get('query', '')}\nAssistant: {msg.get('response', '')[:150]}..."
        for i, msg in enumerate(conversation_history[-3:])
    ])

    prompt = f"""You are a search query optimization assistant. Based on the conversation history, rewrite the user's short query into a complete, clear search query.

Conversation History:
{history_text}

Current Short Query: {query}

Requirements:
- Expand pronouns, abbreviations, and references to full terms
- Keep the query concise but complete
- Only return the rewritten query, nothing else

Rewritten Query:"""

    try:
        from app.utils.llm import generate_response
        rewritten = await generate_response(
            prompt=prompt,
            system_prompt="You are a search query optimization assistant. Only return the rewritten query text, nothing else."
        )
        result = rewritten.strip()
        logger.info(f"Query rewritten: '{query}' -> '{result}'")
        return result if result else query
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}, using original query")
        return query