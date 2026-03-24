"""
Database connection and initialization
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from config import settings
from app.models.database import Base, Intent
import logging

logger = logging.getLogger(__name__)

# Convert SQLite path to async format
db_url = f"sqlite+aiosqlite:///{settings.SQLITE_PATH}"

engine = create_async_engine(
    db_url,
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables and default data"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Create default intents
    async with async_session_maker() as session:
        from sqlalchemy import select

        # Check if intents exist
        result = await session.execute(select(Intent))
        if not result.scalars().first():
            for intent_data in settings.DEFAULT_INTENTS:
                intent = Intent(**intent_data)
                session.add(intent)

            # Add fallback intent
            fallback = Intent(
                name=settings.FALLBACK_INTENT,
                description="通用查询，未能明确分类的意图",
                keywords=[],
                is_default=True
            )
            session.add(fallback)

            await session.commit()
            logger.info("Default intents created")