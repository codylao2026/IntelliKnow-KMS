"""
Document processing service
"""
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Document
from app.utils.document_parser import parse_document, split_text_into_chunks
from app.utils.vectorstore import get_vector_store
from config import settings

logger = logging.getLogger(__name__)


async def process_document(document_id: int, db: AsyncSession, force_rechunk: bool = True) -> bool:
    """
    Process a document: parse, chunk, vectorize

    Args:
        document_id: Database document ID
        db: Database session
        force_rechunk: Force re-chunking even if already processed

    Returns:
        True if successful
    """
    # Get document from database
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        logger.error(f"Document {document_id} not found")
        return False

    try:
        # Update status to processing
        document.status = "processing"
        await db.commit()

        # Delete existing vectors if force_rechunk
        if force_rechunk:
            try:
                vector_store = get_vector_store()
                vector_store.delete_document(document_id)
            except Exception as e:
                logger.warning(f"Could not delete from vector store: {e}")

        # Parse document (only if no content or force_rechunk)
        if not document.content or force_rechunk:
            logger.info(f"Parsing document: {document.file_path}")
            content = parse_document(document.file_path)
            document.content = content
        else:
            logger.info(f"Using existing content for document {document_id}")
            content = document.content

        # Split into chunks
        chunks = split_text_into_chunks(content)
        logger.info(f"Split into {len(chunks)} chunks")

        # Add to vector store
        vector_store = get_vector_store()
        vector_ids = vector_store.add_documents(
            texts=chunks,
            document_id=document_id,
            intent_id=document.intent_id,
            metadata={
                "document_name": document.name,
                "file_type": document.file_type
            }
        )

        # Update document with vector IDs
        document.vector_ids = vector_ids
        document.status = "completed"
        document.error_message = None
        await db.commit()

        logger.info(f"Document {document_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        document.status = "failed"
        document.error_message = str(e)
        await db.commit()
        return False


async def reprocess_document(document_id: int, db: AsyncSession) -> bool:
    """
    Reprocess a document (reparse and re-vectorize)

    Args:
        document_id: Database document ID
        db: Database session

    Returns:
        True if successful
    """
    # Get document
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        logger.error(f"Document {document_id} not found")
        return False

    # Delete from vector store
    try:
        vector_store = get_vector_store()
        vector_store.delete_document(document_id)
    except Exception as e:
        logger.warning(f"Could not delete from vector store: {e}")

    # Clear vector IDs
    document.vector_ids = []

    # Reprocess
    return await process_document(document_id, db)


async def delete_document_from_vector_store(document_id: int) -> bool:
    """
    Delete document from vector store

    Args:
        document_id: Database document ID

    Returns:
        True if successful
    """
    try:
        vector_store = get_vector_store()
        vector_store.delete_document(document_id)
        return True
    except Exception as e:
        logger.error(f"Error deleting from vector store: {e}")
        return False