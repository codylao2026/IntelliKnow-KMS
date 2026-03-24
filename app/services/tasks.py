"""
Background task scheduler for document processing
"""
import asyncio
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Document
from app.services.document_service import process_document
from app.utils.database import async_session_maker

logger = logging.getLogger(__name__)

# Thread pool for CPU-bound tasks
_executor = ThreadPoolExecutor(max_workers=2)
_processing_tasks: dict = {}


async def process_document_async(document_id: int, force_rechunk: bool = True):
    """
    Process document asynchronously

    Args:
        document_id: Document ID to process
        force_rechunk: Force re-chunking even if document was processed before
    """
    import os
    task_id = f"doc_{document_id}"
    _processing_tasks[task_id] = "processing"

    logger.info(f"Starting async processing for document {document_id}, force_rechunk={force_rechunk}")

    try:
        # Wait a bit to ensure file is fully written
        await asyncio.sleep(0.5)

        # Verify file exists before processing
        async with async_session_maker() as db:
            from sqlalchemy import select
            from app.models.database import Document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            
            if doc and doc.file_path:
                if not os.path.exists(doc.file_path):
                    logger.error(f"File does not exist: {doc.file_path}")
                    _processing_tasks[task_id] = "failed"
                    return
                    
                # Check file size is reasonable
                file_size = os.path.getsize(doc.file_path)
                if file_size == 0:
                    logger.error(f"File is empty: {doc.file_path}")
                    _processing_tasks[task_id] = "failed"
                    return
                    
                logger.info(f"Processing file: {doc.file_path}, size: {file_size} bytes")

            success = await process_document(document_id, db, force_rechunk=force_rechunk)

            if success:
                _processing_tasks[task_id] = "completed"
                logger.info(f"Document {document_id} processed successfully")
            else:
                _processing_tasks[task_id] = "failed"
                logger.error(f"Document {document_id} processing failed")

    except Exception as e:
        _processing_tasks[task_id] = "failed"
        logger.error(f"Error in async document processing: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    finally:
        # Clean up after a delay
        await asyncio.sleep(60)  # Keep status for 60 seconds
        _processing_tasks.pop(task_id, None)


def get_processing_status(document_id: int) -> Optional[str]:
    """Get processing status for a document"""
    task_id = f"doc_{document_id}"
    return _processing_tasks.get(task_id)


async def process_pending_documents():
    """Process all pending documents"""
    logger.info("Checking for pending documents...")

    async with async_session_maker() as db:
        result = await db.execute(
            select(Document).where(Document.status == "pending")
        )
        pending_docs = result.scalars().all()

        logger.info(f"Found {len(pending_docs)} pending documents")

        for doc in pending_docs:
            task_id = f"doc_{doc.id}"
            if task_id not in _processing_tasks:
                asyncio.create_task(process_document_async(doc.id))
                logger.info(f"Queued document {doc.id} for processing")


async def start_task_scheduler():
    """Start the background task scheduler"""
    logger.info("Starting task scheduler")

    while True:
        try:
            await process_pending_documents()
        except Exception as e:
            logger.error(f"Error in task scheduler: {e}")

        # Check every 10 seconds
        await asyncio.sleep(10)