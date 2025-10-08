"""
Test script for database setup and operations

This script tests:
1. Database connection
2. SQLAlchemy models
3. DatabaseService CRUD operations

Run this script to verify the database integration:
    python test_database.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import check_db_connection
from app.services.database_service import DatabaseService
from app.models.database_models import User, Session, Cluster
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Single instance for all tests
db_service = DatabaseService()


def test_connection():
    """Test database connection"""
    logger.info("=" * 60)
    logger.info("TEST 1: Database Connection")
    logger.info("=" * 60)
    
    result = check_db_connection()
    assert result, "❌ Database connection failed"
    logger.info("✅ Database connection successful\n")


def test_user_operations():
    """Test user CRUD operations"""
    logger.info("=" * 60)
    logger.info("TEST 2: User Operations")
    logger.info("=" * 60)
    
    # Test get or create user
    test_email = "test_user@example.com"
    user = db_service.get_or_create_user(test_email, "Test User")
    assert user is not None, "❌ Failed to create user"
    logger.info(f"✅ Created/retrieved user: {user}")
    
    # Test idempotency (should return same user)
    user2 = db_service.get_or_create_user(test_email, "Test User")
    assert user2.id == user.id, "❌ Should return same user"
    logger.info(f"✅ Get or create is idempotent\n")
    
    return user


def test_session_operations(user: User):
    """Test session CRUD operations"""
    logger.info("=" * 60)
    logger.info("TEST 3: Session Operations")
    logger.info("=" * 60)
    
    # Test create session
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=2)
    
    session = db_service.create_session(
        user_id=user.id,
        start_time=start_time,
        end_time=end_time
    )
    assert session is not None, "❌ Failed to create session"
    logger.info(f"✅ Created session: {session}\n")
    
    return session


def test_cluster_operations(session: Session):
    """Test cluster CRUD operations"""
    logger.info("=" * 60)
    logger.info("TEST 4: Cluster Operations")
    logger.info("=" * 60)
    
    # Test create cluster
    cluster = db_service.create_cluster(
        session_id=session.id,
        name="Web Development",
        description="Research on React and FastAPI development"
    )
    assert cluster is not None, "❌ Failed to create cluster"
    logger.info(f"✅ Created cluster: {cluster}\n")
    
    return cluster


def test_history_item_operations(cluster: Cluster):
    """Test history item CRUD operations"""
    logger.info("=" * 60)
    logger.info("TEST 5: History Item Operations")
    logger.info("=" * 60)
    
    # Test create history item
    item = db_service.create_history_item(
        cluster_id=cluster.id,
        url="https://fastapi.tiangolo.com/",
        title="FastAPI Documentation",
        domain="fastapi.tiangolo.com",
        visit_time=datetime.now(),
        raw_semantics={
            "url_pathname": "/",
            "keywords": ["fastapi", "python", "api"]
        }
    )
    assert item is not None, "❌ Failed to create history item"
    logger.info(f"✅ Created history item: {item}\n")
    
    return item


def main():
    """Run all tests"""
    try:
        logger.info("\n🚀 Starting database tests...\n")
        
        # Test 1: Connection
        test_connection()
        
        # Test 2: User operations
        user = test_user_operations()
        
        # Test 3: Session operations
        session = test_session_operations(user)
        
        # Test 4: Cluster operations
        cluster = test_cluster_operations(session)
        
        # Test 5: History item operations
        item = test_history_item_operations(cluster)
        
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\n🎉 Database integration is working correctly!\n")
        
    except AssertionError as e:
        logger.error(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ UNEXPECTED ERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
