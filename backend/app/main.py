from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime

from .services.clustering_service import ClusteringService
from .services.llm_service import LLMService
from .models.session_models import HistorySession, ClusterResult, SessionClusteringResponse
from .models.llm_models import LLMRequest, LLMResponse, LLMProvider

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

@app.post("/cluster", response_model=Dict[str, SessionClusteringResponse])
async def cluster_sessions(sessions: List[HistorySession]):
    """
    Cluster browsing history sessions into thematic groups, processing each session independently
    
    Args:
        sessions: List of browsing history sessions
        
    Returns:
        Dict mapping session_id to SessionClusteringResponse with clusters for each session
    """
    try:
        logger.info(f"Received {len(sessions)} sessions for clustering")
        
        if not sessions:
            raise HTTPException(status_code=400, detail="No sessions provided")
        
        # Process sessions through clustering service
        session_results = await clustering_service.cluster_sessions(sessions)
        
        logger.info(f"Generated clustering results for {len(session_results)} sessions")
        return session_results
        
    except Exception as e:
        logger.error(f"Error clustering sessions: {str(e)}")
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

@app.get("/llm/providers")
async def get_available_providers():
    """Get list of available LLM providers"""
    try:
        providers = llm_service.get_available_providers()
        return {
            "available_providers": [provider.value for provider in providers],
            "count": len(providers)
        }
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
