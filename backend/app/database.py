from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def check_db_connection() -> bool:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection healthy")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

