"""
IntelliKnow KMS - FastAPI Application
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

from config import settings
from app.utils.database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting IntelliKnow KMS...")
    await init_db()
    logger.info("Database initialized")

    # Initialize Feishu client (long connection mode)
    try:
        from app.services.frontend.feishu import init_feishu_client

        if init_feishu_client():
            logger.info("Feishu client started successfully")
        else:
            logger.warning("Feishu client not configured or failed to start")
    except Exception as e:
        logger.warning(f"Feishu initialization skipped: {e}")

    # Initialize Telegram client (polling mode)
    try:
        from app.services.frontend.telegram import init_telegram_client
        from config import settings

        if settings.TELEGRAM_POLLING_ENABLED and settings.TELEGRAM_BOT_TOKEN:
            if init_telegram_client():
                logger.info("Telegram client started successfully")
            else:
                logger.warning("Telegram client not configured")
        else:
            logger.info("Telegram polling disabled")
    except Exception as e:
        logger.warning(f"Telegram initialization skipped: {e}")

    yield
    # Shutdown
    logger.info("Shutting down IntelliKnow KMS...")

    # Stop Telegram client
    try:
        from app.services.frontend.telegram import get_telegram_client

        client = get_telegram_client()
        if client.is_running():
            client.stop()
            logger.info("Telegram client stopped")
    except Exception as e:
        logger.warning(f"Telegram shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="IntelliKnow KMS",
    description="Gen AI-powered Knowledge Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IntelliKnow KMS"}


# API routes
from app.api import documents, intents, query, analytics, webhooks, credentials

app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(intents.router, prefix="/api/intents", tags=["Intents"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(credentials.router, prefix="/api/credentials", tags=["Credentials"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True
    )
