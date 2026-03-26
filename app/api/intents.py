"""
Intent API routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from pydantic import BaseModel

from app.utils.database import get_db
from app.models.database import Intent, Document
from app.models.schemas import IntentCreate, IntentUpdate, IntentResponse
from app.services.intent_service import (
    get_confidence_settings,
    save_confidence_settings,
    invalidate_intent_cache,
)
from config import settings

router = APIRouter()


class ConfidenceSettingsResponse(BaseModel):
    confidence_threshold: float
    llm_weight: float
    keyword_weight: float


class ConfidenceSettingsUpdate(BaseModel):
    confidence_threshold: float
    llm_weight: float = 0.5
    keyword_weight: float = 0.5


class DocumentSettingsResponse(BaseModel):
    chunk_size: int
    chunk_overlap: int


class DocumentSettingsUpdate(BaseModel):
    chunk_size: int
    chunk_overlap: int


@router.get("/settings/confidence", response_model=ConfidenceSettingsResponse)
async def get_confidence_config(db: AsyncSession = Depends(get_db)):
    """Get confidence classification settings"""
    settings = await get_confidence_settings(db)
    return ConfidenceSettingsResponse(
        confidence_threshold=settings["confidence_threshold"],
        llm_weight=settings["llm_weight"],
        keyword_weight=settings["keyword_weight"],
    )


@router.put("/settings/confidence", response_model=ConfidenceSettingsResponse)
async def update_confidence_config(
    config: ConfidenceSettingsUpdate, db: AsyncSession = Depends(get_db)
):
    """Update confidence classification settings"""
    await save_confidence_settings(
        db=db,
        confidence_threshold=config.confidence_threshold,
        llm_weight=config.llm_weight,
        keyword_weight=config.keyword_weight,
    )
    return ConfidenceSettingsResponse(
        confidence_threshold=config.confidence_threshold,
        llm_weight=config.llm_weight,
        keyword_weight=config.keyword_weight,
    )


@router.get("/settings/document", response_model=DocumentSettingsResponse)
async def get_document_config():
    """Get document processing settings"""
    return DocumentSettingsResponse(
        chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
    )


@router.put("/settings/document", response_model=DocumentSettingsResponse)
async def update_document_config(config: DocumentSettingsUpdate):
    """Update document processing settings"""
    settings.CHUNK_SIZE = config.chunk_size
    settings.CHUNK_OVERLAP = config.chunk_overlap
    return DocumentSettingsResponse(
        chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
    )


@router.get("", response_model=List[IntentResponse])
async def list_intents(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """List all intent spaces"""
    result = await db.execute(select(Intent).offset(skip).limit(limit))
    intents = result.scalars().all()

    # Get document count for each intent
    intent_responses = []
    for intent in intents:
        doc_count_result = await db.execute(
            select(func.count(Document.id)).where(Document.intent_id == intent.id)
        )
        doc_count = doc_count_result.scalar() or 0

        intent_responses.append(
            IntentResponse(
                id=intent.id,
                name=intent.name,
                description=intent.description,
                keywords=intent.keywords or [],
                is_default=intent.is_default,
                created_at=intent.created_at,
                updated_at=intent.updated_at,
                document_count=doc_count,
            )
        )

    return intent_responses


@router.get("/{intent_id}", response_model=IntentResponse)
async def get_intent(intent_id: int, db: AsyncSession = Depends(get_db)):
    """Get intent by ID"""
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    # Get document count
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.intent_id == intent.id)
    )
    doc_count = doc_count_result.scalar() or 0

    return IntentResponse(
        id=intent.id,
        name=intent.name,
        description=intent.description,
        keywords=intent.keywords or [],
        is_default=intent.is_default,
        created_at=intent.created_at,
        updated_at=intent.updated_at,
        document_count=doc_count,
    )


@router.post("", response_model=IntentResponse)
async def create_intent(intent_data: IntentCreate, db: AsyncSession = Depends(get_db)):
    """Create new intent space"""
    # Check for duplicate name
    result = await db.execute(select(Intent).where(Intent.name == intent_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Intent name already exists")

    intent = Intent(
        name=intent_data.name,
        description=intent_data.description,
        keywords=intent_data.keywords,
        is_default=False,
    )
    db.add(intent)
    await db.commit()
    await db.refresh(intent)

    # Invalidate intent cache
    invalidate_intent_cache()

    return IntentResponse(
        id=intent.id,
        name=intent.name,
        description=intent.description,
        keywords=intent.keywords or [],
        is_default=intent.is_default,
        created_at=intent.created_at,
        updated_at=intent.updated_at,
        document_count=0,
    )


@router.put("/{intent_id}", response_model=IntentResponse)
async def update_intent(
    intent_id: int, intent_data: IntentUpdate, db: AsyncSession = Depends(get_db)
):
    """Update intent space"""
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    # Check for duplicate name if name is being changed
    if intent_data.name and intent_data.name != intent.name:
        dup_result = await db.execute(
            select(Intent).where(Intent.name == intent_data.name)
        )
        if dup_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Intent name already exists")

    # Update fields
    if intent_data.name is not None:
        intent.name = intent_data.name
    if intent_data.description is not None:
        intent.description = intent_data.description
    if intent_data.keywords is not None:
        intent.keywords = intent_data.keywords

    await db.commit()
    await db.refresh(intent)

    # Invalidate intent cache
    invalidate_intent_cache()

    # Get document count
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.intent_id == intent.id)
    )
    doc_count = doc_count_result.scalar() or 0

    return IntentResponse(
        id=intent.id,
        name=intent.name,
        description=intent.description,
        keywords=intent.keywords or [],
        is_default=intent.is_default,
        created_at=intent.created_at,
        updated_at=intent.updated_at,
        document_count=doc_count,
    )


@router.delete("/{intent_id}")
async def delete_intent(intent_id: int, db: AsyncSession = Depends(get_db)):
    """Delete intent space"""
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    # Check if intent has documents
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.intent_id == intent_id)
    )
    doc_count = doc_count_result.scalar() or 0

    if doc_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete intent with {doc_count} associated documents",
        )

    # Check if it's the fallback intent
    if intent.name == "通用":
        raise HTTPException(status_code=400, detail="Cannot delete fallback intent")

    await db.delete(intent)
    await db.commit()

    # Invalidate intent cache
    invalidate_intent_cache()

    return {"message": "Intent deleted successfully"}
