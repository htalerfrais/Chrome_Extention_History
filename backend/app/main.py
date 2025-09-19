from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime

from .services.clustering_service import ClusteringService
from .models.session_models import HistorySession, ClusterResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chrome Extension History Clustering API",
    description="API for clustering browsing history into thematic sessions",
    version="0.2.0"
)

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clustering service
clustering_service = ClusteringService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Chrome Extension History Clustering API",
        "version": "0.2.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "clustering": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/cluster", response_model=List[ClusterResult])
async def cluster_sessions(sessions: List[HistorySession]):
    """
    Cluster browsing history sessions into thematic groups
    
    Args:
        sessions: List of browsing history sessions
        
    Returns:
        List of cluster results with thematic groupings
    """
    try:
        logger.info(f"Received {len(sessions)} sessions for clustering")
        
        if not sessions:
            raise HTTPException(status_code=400, detail="No sessions provided")
        
        # Process sessions through clustering service
        clusters = await clustering_service.cluster_sessions(sessions)
        
        logger.info(f"Generated {len(clusters)} clusters")
        return clusters
        
    except Exception as e:
        logger.error(f"Error clustering sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
