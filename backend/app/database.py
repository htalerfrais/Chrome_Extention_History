"""
Database configuration and session management

This module provides:
- Engine: Connection pool to PostgreSQL
- SessionLocal: Factory for creating database sessions
- check_db_connection: Health check for database

Usage in services:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        db.commit()
    finally:
        db.close()
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create engine with connection pool
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
    """
    Check database connection health
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection healthy")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

