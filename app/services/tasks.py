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


async def process_document_async(document_id: int):
    """
    Process document asynchronously

    Args:
        document_id: Document ID to process
    """
    task_id = f"doc_{document_id}"
    _processing_tasks[task_id] = "processing"

    logger.info(f"Starting async processing for document {document_id}")

    try:
        async with async_session_maker() as db:
            success = await process_document(document_id, db)

            if success:
                _processing_tasks[task_id] = "completed"
                logger.info(f"Document {document_id} processed successfully")
            else:
                _processing_tasks[task_id] = "failed"
                logger.error(f"Document {document_id} processing failed")

    except Exception as e:
        _processing_tasks[task_id] = "failed"
        logger.error(f"Error in async document processing: {e}")

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