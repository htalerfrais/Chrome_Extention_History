from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class HistoryItem(BaseModel):
    """Individual browsing history item"""
    id: str
    url: str
    title: str
    visit_time: datetime
    visit_count: int = 1
    typed_count: int = 0
    last_visit_time: Optional[datetime] = None
    # Optional enriched URL features from the extension
    url_hostname: Optional[str] = None
    url_pathname_clean: Optional[str] = None
    url_search_query: Optional[str] = None

class HistorySession(BaseModel):
    """A session of browsing history items grouped by time"""
    session_id: str
    start_time: datetime
    end_time: datetime
    items: List[HistoryItem]
    duration_minutes: Optional[int] = None
    
    def __post_init__(self):
        if self.duration_minutes is None:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)

class ClusterItem(BaseModel):
    """A history item within a cluster"""
    id: str
    url: str
    title: str
    visit_time: datetime
    session_id: str

    # Optional enriched URL features propagated from HistoryItem
    url_hostname: Optional[str] = None
    url_pathname_clean: Optional[str] = None
    url_search_query: Optional[str] = None

class ClusterResult(BaseModel):
    """Result of clustering algorithm"""
    cluster_id: str
    theme: str
    items: List[ClusterItem]

class ClusteringRequest(BaseModel):
    """Request model for clustering endpoint"""
    sessions: List[HistorySession]
    max_clusters: Optional[int] = Field(default=10, ge=1, le=50)
    min_cluster_size: Optional[int] = Field(default=2, ge=1)

class SessionClusteringResponse(BaseModel):
    """Response model for session-based clustering"""
    session_id: str
    session_start_time: datetime
    session_end_time: datetime
    clusters: List[ClusterResult]
    
