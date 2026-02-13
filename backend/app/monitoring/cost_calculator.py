"""
Cost calculator for LLM API usage.

Provides functions to estimate costs based on token usage and provider pricing.
Pricing data is hardcoded and should be updated when providers change their rates.
"""

from typing import Dict, Any, Optional

# Pricing per 1K tokens (as of February 2026)
PRICING: Dict[str, Dict[str, Dict[str, float]]] = {
    "google": {
        "gemini-2.0-flash": {
            "input": 0.00001875,   # $0.00001875 per 1K input tokens
            "output": 0.000075     # $0.000075 per 1K output tokens
        },
        "gemini-1.5-flash": {
            "input": 0.000075,
            "output": 0.0003
        },
        "gemini-1.5-pro": {
            "input": 0.00125,
            "output": 0.005
        },
        "gemini-embedding-001": {
            "embedding": 0.00001  # $0.00001 per 1K tokens
        }
    },
    "openai": {
        "gpt-4o": {
            "input": 0.0025,       # $2.50 per 1M tokens
            "output": 0.01         # $10 per 1M tokens
        },
        "gpt-4o-mini": {
            "input": 0.00015,
            "output": 0.0006
        },
        "gpt-3.5-turbo": {
            "input": 0.0005,
            "output": 0.0015
        },
        "text-embedding-3-small": {
            "embedding": 0.00002
        },
        "text-embedding-3-large": {
            "embedding": 0.00013
        }
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "input": 0.003,
            "output": 0.015
        },
        "claude-3-opus-20240229": {
            "input": 0.015,
            "output": 0.075
        },
        "claude-3-haiku-20240307": {
            "input": 0.00025,
            "output": 0.00125
        }
    }
}

def calculate_llm_cost(
    provider: str, 
    model: str, 
    tokens_in: int, 
    tokens_out: int
) -> float:
    """
    Calculate the cost of an LLM API call based on token usage.
    
    Args:
        provider: LLM provider name (e.g., "google", "openai", "anthropic")
        model: Model name (e.g., "gemini-2.0-flash", "gpt-4o")
        tokens_in: Number of input tokens
        tokens_out: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    if provider not in PRICING:
        return 0.0
    
    if model not in PRICING[provider]:
        return 0.0
    
    pricing = PRICING[provider][model]
    
    # Check if this is an embedding model (different pricing structure)
    if "embedding" in pricing:
        return 0.0  # Use calculate_embedding_cost for embeddings
    
    input_cost = (tokens_in / 1000) * pricing.get("input", 0)
    output_cost = (tokens_out / 1000) * pricing.get("output", 0)
    
    return input_cost + output_cost

def calculate_embedding_cost(
    provider: str, 
    model: str, 
    text_count: int
) -> float:
    """
    Calculate the cost of embedding generation.
    
    Args:
        provider: Provider name (e.g., "google", "openai")
        model: Model name (e.g., "gemini-embedding-001")
        text_count: Number of texts embedded (approximation for token count)
        
    Returns:
        Estimated cost in USD
    """
    if provider not in PRICING:
        return 0.0
    
    if model not in PRICING[provider]:
        return 0.0
    
    pricing = PRICING[provider][model]
    
    if "embedding" not in pricing:
        return 0.0
    
    # Rough approximation: 1 text ≈ 50 tokens on average
    estimated_tokens = text_count * 50
    cost = (estimated_tokens / 1000) * pricing["embedding"]
    
    return cost

def get_model_pricing(provider: str, model: str) -> Optional[Dict[str, float]]:
    """
    Get pricing information for a specific model.
    
    Args:
        provider: Provider name
        model: Model name
        
    Returns:
        Dictionary with pricing info or None if not found
    """
    if provider not in PRICING:
        return None
    
    if model not in PRICING[provider]:
        return None
    
    return PRICING[provider][model]
