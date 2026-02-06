from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
from pgvector.sqlalchemy import Vector

# Base class for all models
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    google_user_id = Column(String, unique=True, nullable=False, index=True)
    token = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, google_user_id='{self.google_user_id}')>"


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_identifier = Column(String, nullable=False, unique=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    user = relationship("User", back_populates="sessions")
    clusters = relationship("Cluster", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, session_identifier='{self.session_identifier}')>"


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
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    session = relationship("Session", back_populates="clusters")
    history_items = relationship("HistoryItem", back_populates="cluster", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cluster(id={self.id}, session_id={self.session_id}, name='{self.name}')>"


class HistoryItem(Base):
    __tablename__ = "history_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    visit_time = Column(DateTime, nullable=False)
    raw_semantics = Column(JSON, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    cluster = relationship("Cluster", back_populates="history_items")
    
    def __repr__(self):
        return f"<HistoryItem(id={self.id}, cluster_id={self.cluster_id}, url='{self.url}')>"

