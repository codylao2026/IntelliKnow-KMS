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
    logger.info(f"Starting to process document {document_id}, force_rechunk={force_rechunk}")
    
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
        logger.info(f"Document {document_id} status changed to processing")

        # Delete existing vectors if force_rechunk
        if force_rechunk:
            try:
                vector_store = get_vector_store()
                vector_store.delete_document(document_id)
                logger.info(f"Deleted existing vectors for document {document_id}")
            except Exception as e:
                logger.warning(f"Could not delete from vector store: {e}")

        # Parse document - always prefer database content if it exists (edited content)
        # Only re-parse if force_rechunk=True or no content exists
        old_content = document.content if document.content else ""
        is_error_content = old_content.startswith("[Unable to extract")
        
        if document.content and not force_rechunk and not is_error_content:
            # Use content from database (could be edited content)
            logger.info(f"Using database content for document {document_id}, length: {len(document.content)}")
            content = document.content
        else:
            # Parse from file (or re-parse for rechunk)
            logger.info(f"Parsing document from file: {document.file_path}")
            content = parse_document(document.file_path)
            
            # Only update content if parsing succeeded
            if content and not content.startswith("[Unable to extract"):
                document.content = content
                logger.info(f"Document {document_id} parsed from file, content length: {len(content)}")
            elif is_error_content:
                # Keep old content if new parsing failed
                content = old_content
                logger.warning(f"Keeping old content for document {document_id} - new parse failed")
            else:
                logger.warning(f"Document {document_id} parse returned empty content")

        # Split into chunks
        chunks = split_text_into_chunks(content)
        logger.info(f"Document {document_id} split into {len(chunks)} chunks")

        # Add to vector store
        vector_store = get_vector_store()
        logger.info(f"Adding {len(chunks)} chunks to vector store for document {document_id}")
        vector_ids = vector_store.add_documents(
            texts=chunks,
            document_id=document_id,
            intent_id=document.intent_id,
            metadata={
                "document_name": document.name,
                "file_type": document.file_type
            }
        )
        logger.info(f"Document {document_id} added to vector store, got {len(vector_ids)} vector IDs")

        # Update document with vector IDs
        document.vector_ids = vector_ids
        document.status = "completed"
        document.error_message = None
        await db.commit()

        logger.info(f"Document {document_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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