from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime

from .services.clustering_service import ClusteringService
from .services.llm_service import LLMService
from .models.session_models import HistorySession, ClusterResult, SessionClusteringResponse
from .models.llm_models import LLMRequest, LLMResponse

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

# Initialize services
clustering_service = ClusteringService()
llm_service = LLMService()

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
            "clustering": "operational",
            "llm": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/cluster-session", response_model=SessionClusteringResponse)
async def cluster_session(session: HistorySession):
    """
    Cluster a single browsing history session into thematic groups
    
    Args:
        session: Single browsing history session to cluster
        
    Returns:
        SessionClusteringResponse with clusters for the session
    """
    try:
        logger.info(f"Received session {session.session_id} with {len(session.items)} items for clustering")
        
        if not session.items:
            raise HTTPException(status_code=400, detail="Session has no items to cluster")
        
        # Process single session through clustering service
        session_result = await clustering_service.cluster_session(session)
        
        logger.info(f"Generated clustering result for session {session.session_id} with {len(session_result.clusters)} clusters")
        return session_result
        
    except Exception as e:
        logger.error(f"Error clustering session {getattr(session, 'session_id', 'unknown')}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")

@app.post("/llm/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    """
    Generate text using specified LLM provider
    
    Args:
        request: LLM generation request with prompt and provider settings
        
    Returns:
        LLMResponse with generated text and metadata
    """
    try:
        logger.info(f"Received LLM request for provider: {request.provider}")
        
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        # Generate text using LLM service
        response = await llm_service.generate_text(request)
        
        logger.info(f"Successfully generated text with {request.provider}")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid LLM request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
