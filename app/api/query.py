"""
Query API routes - RAG pipeline
"""
import logging
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.models.schemas import QueryRequest, QueryResponse, QuerySource
from app.services.response_service import process_query, process_query_streaming

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the knowledge base with full RAG pipeline:
    1. Intent classification
    2. Query rewrite (optional)
    3. Hybrid search (BM25 + Vector)
    4. Rerank
    5. Response generation
    """
    result = await process_query(
        query=request.query,
        db=db,
        frontend=request.frontend,
        intent_hint=request.intent_hint
    )

    # Convert sources to QuerySource format
    sources = [
        QuerySource(
            document_id=s["document_id"],
            document_name=s["document_name"],
            content=s["content"],
            score=s["score"]
        )
        for s in result.get("sources", [])
    ]

    return QueryResponse(
        query=result["query"],
        response=result["response"],
        intent=result["intent"],
        confidence=result["confidence"],
        confidence_source=result.get("confidence_source"),
        sources=sources,
        response_time=result["response_time"],
        status=result["status"]
    )


@router.post("/stream")
async def query_knowledge_base_stream(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Streaming version of query endpoint for better UX.
    Returns Server-Sent Events (SSE) stream.
    """
    return StreamingResponse(
        process_query_streaming(
            query=request.query,
            db=db,
            frontend=request.frontend,
            intent_hint=request.intent_hint
        ),
        media_type="text/event-stream"
    )


@router.get("/history")
async def get_query_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get query history"""
    from sqlalchemy import select
    from app.models.database import QueryLog

    result = await db.execute(
        select(QueryLog)
        .order_by(QueryLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "query": log.query,
                "intent_name": log.intent_name,
                "confidence": log.confidence,
                "status": log.status,
                "response_time": log.response_time,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": len(logs)
    }