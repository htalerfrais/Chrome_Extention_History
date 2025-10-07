from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime

from .services.clustering_service import ClusteringService
from .services.llm_service import LLMService
from .services.chat_service import ChatService
from .models.session_models import HistorySession, ClusterResult, SessionClusteringResponse
from .models.llm_models import LLMRequest, LLMResponse
from .models.chat_models import ChatRequest, ChatResponse

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
chat_service = ChatService(llm_service)

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
            "llm": "operational",
            "chat": "operational"
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


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for conversational interaction
    
    Phase 1: Simple LLM chat with conversation context
    Phase 2: Will integrate with history data and tool calling
    """
    try:
        logger.info(f"Received chat message: {request.message[:50]}...")
        
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Process message through chat service
        response = await chat_service.process_message(request)
        
        logger.info(f"Chat response generated for conversation {response.conversation_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
