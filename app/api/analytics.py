"""
Analytics API routes
"""
import csv
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.utils.database import get_db
from app.models.database import QueryLog, Document, Intent
from app.models.schemas import (
    DashboardStats, QueryLogResponse, QueryLogListResponse,
    IntentStats, PopularDocument, AnalyticsResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    # Total queries
    total_result = await db.execute(select(func.count(QueryLog.id)))
    total_queries = total_result.scalar() or 0

    # Today's queries
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(QueryLog.id)).where(QueryLog.created_at >= today_start)
    )
    today_queries = today_result.scalar() or 0

    # Accuracy (queries with confidence >= 0.7)
    accuracy_result = await db.execute(
        select(func.count(QueryLog.id)).where(QueryLog.confidence >= 0.7)
    )
    accurate_queries = accuracy_result.scalar() or 0
    accuracy = (accurate_queries / total_queries * 100) if total_queries > 0 else 0.0

    # Document count
    doc_result = await db.execute(
        select(func.count(Document.id)).where(Document.status == "completed")
    )
    document_count = doc_result.scalar() or 0

    # Intent count
    intent_result = await db.execute(select(func.count(Intent.id)))
    intent_count = intent_result.scalar() or 0

    return DashboardStats(
        total_queries=total_queries,
        today_queries=today_queries,
        accuracy=round(accuracy, 2),
        document_count=document_count,
        intent_count=intent_count
    )


@router.get("/logs", response_model=QueryLogListResponse)
async def get_query_logs(
    skip: int = 0,
    limit: int = 50,
    intent_name: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get query logs with filters"""
    query = select(QueryLog)

    if intent_name:
        query = query.where(QueryLog.intent_name == intent_name)
    if status:
        query = query.where(QueryLog.status == status)

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    # Get logs
    query = query.order_by(QueryLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        QueryLogResponse(
            id=log.id,
            query=log.query,
            intent_name=log.intent_name,
            confidence=log.confidence,
            response=log.response,
            frontend=log.frontend,
            status=log.status,
            response_time=log.response_time,
            created_at=log.created_at
        )
        for log in logs
    ]

    return QueryLogListResponse(items=items, total=total)


@router.get("/intents", response_model=list)
async def get_intent_stats(db: AsyncSession = Depends(get_db)):
    """Get intent usage statistics"""
    # Get query counts and accuracy per intent
    intents_result = await db.execute(select(Intent))
    intents = intents_result.scalars().all()

    stats = []
    for intent in intents:
        # Query count
        count_result = await db.execute(
            select(func.count(QueryLog.id)).where(QueryLog.intent_name == intent.name)
        )
        query_count = count_result.scalar() or 0

        # Accuracy (confidence >= 0.7)
        acc_result = await db.execute(
            select(func.count(QueryLog.id)).where(
                QueryLog.intent_name == intent.name,
                QueryLog.confidence >= 0.7
            )
        )
        accurate = acc_result.scalar() or 0
        accuracy = (accurate / query_count * 100) if query_count > 0 else 0.0

        stats.append(IntentStats(
            intent_name=intent.name,
            query_count=query_count,
            accuracy=round(accuracy, 2)
        ))

    # Sort by query count descending
    stats.sort(key=lambda x: x.query_count, reverse=True)

    return stats


@router.get("/popular-documents", response_model=list)
async def get_popular_documents(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get popular documents by access count"""
    # Group by document and count accesses
    result = await db.execute(
        select(
            QueryLog.document_id,
            func.count(QueryLog.id).label("access_count")
        )
        .where(QueryLog.document_id.isnot(None))
        .group_by(QueryLog.document_id)
        .order_by(func.count(QueryLog.id).desc())
        .limit(limit)
    )
    rows = result.all()

    popular = []
    for row in rows:
        # Get document name
        doc_result = await db.execute(
            select(Document.name).where(Document.id == row.document_id)
        )
        doc_name = doc_result.scalar_one_or_none() or "Unknown"

        popular.append(PopularDocument(
            document_id=row.document_id,
            document_name=doc_name,
            access_count=row.access_count
        ))

    return popular


@router.get("/export-logs")
async def export_query_logs_csv(
    db: AsyncSession = Depends(get_db)
):
    """Export query logs as CSV"""
    result = await db.execute(
        select(QueryLog).order_by(QueryLog.created_at.desc()).limit(1000)
    )
    logs = result.scalars().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Query", "Intent", "Confidence", "Frontend",
        "Status", "Response Time (ms)", "Created At"
    ])

    for log in logs:
        writer.writerow([
            log.id,
            log.query,
            log.intent_name,
            log.confidence,
            log.frontend,
            log.status,
            log.response_time,
            log.created_at.isoformat()
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=query_logs.csv"}
    )