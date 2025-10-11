"""
SQLAlchemy models for database tables

These models map Python classes to PostgreSQL tables and handle:
- Table structure and relationships
- Foreign key constraints
- Vector columns for embeddings (pgvector)
- Automatic timestamps

Note: These are separate from Pydantic models (session_models.py)
- Pydantic = API validation and serialization
- SQLAlchemy = Database mapping and queries
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
from pgvector.sqlalchemy import Vector

# Base class for all models
Base = declarative_base()


class User(Base):
    """
    User model - represents users of the Chrome extension
    
    Relationships:
    - One user has many sessions
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    token = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class Session(Base):
    """
    Session model - represents browsing sessions grouped by time
    
    Relationships:
    - One session belongs to one user
    - One session has many clusters
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    user = relationship("User", back_populates="sessions")
    clusters = relationship("Cluster", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, start_time='{self.start_time}')>"


class Cluster(Base):
    """
    Cluster model - represents thematic groups within a session
    
    Relationships:
    - One cluster belongs to one session
    - One cluster has many history items
    """
    __tablename__ = "clusters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    session = relationship("Session", back_populates="clusters")
    history_items = relationship("HistoryItem", back_populates="cluster", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cluster(id={self.id}, session_id={self.session_id}, name='{self.name}')>"


class HistoryItem(Base):
    """
    HistoryItem model - represents individual browsing history entries
    
    Relationships:
    - One history item belongs to one cluster
    """
    __tablename__ = "history_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    visit_time = Column(DateTime, nullable=False)
    raw_semantics = Column(JSON, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    cluster = relationship("Cluster", back_populates="history_items")
    
    def __repr__(self):
        return f"<HistoryItem(id={self.id}, cluster_id={self.cluster_id}, url='{self.url}')>"

