from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

# Load .env file for local development (when not in Docker)
if not os.getenv("DOCKER_CONTAINER"):
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)


#- file config actually uses pydantic BaseSettings model and is overridden by .env . 
# class Config acknowledges what env file to read to fill in the settings
# - **Key Point**: .env is for **"what changes between environments"**, config.py is for **"how the app works"**

class Settings(BaseSettings):
    # Application
    app_name: str = "Chrome Extension History Clustering API"
    app_version: str = "0.2.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = [
        "chrome-extension://*", 
        "http://localhost:*"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    
    # API Keys (from environment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # LLM Configuration
    default_provider: str = "google"
    default_model: str = "gemini-2.0-flash"
    
    # Clustering Service
    clustering_batch_size: int = 20
    clustering_max_tokens: int = 16384
    clustering_temperature: float = 0.2
    clustering_similarity_threshold: float = 0.35  # cosine similarity threshold for cluster assignment
    # Current session detection window (minutes)
    current_session_gap_minutes: int = 30
    
    # Chat Service  
    chat_max_tokens: int = 8000
    chat_temperature: float = 0.7
    chat_history_limit: int = 10
    
    # Embeddings
    embedding_provider: str = "google"
    embedding_model: str = "text-embedding-004"  # Returns 768 dimensions
    embedding_dim: int = 768  # text-embedding-004 outputs 768 dimensions

    # Provider URLs
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_base_url: str = "https://api.anthropic.com"
    google_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    ollama_base_url: str = "http://localhost:11434"
    
    # Timeouts
    api_timeout: float = 30.0
    ollama_timeout: float = 60.0
    
    # Database
    database_url: Optional[str] = None
    
    class Config:
        # Docker Compose passes environment variables directly
        # Local development: set environment variables or use .env
        case_sensitive = False

# Global settings instance
settings = Settings()
