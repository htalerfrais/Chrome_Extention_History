"""
Monitoring package for logging, metrics, and performance tracking.

This package provides:
- Request tracing via contextvars
- In-memory metrics collection
- Performance decorators
- Structured JSON logging
- LLM cost estimation
"""

from .context import request_id_var, get_request_id, set_request_id
from .metrics import metrics, MetricsCollector
from .decorators import track_performance, track_llm_call
from .logger_config import configure_logging, CustomJsonFormatter, RequestIdFilter
from .cost_calculator import calculate_llm_cost, calculate_embedding_cost, get_model_pricing

__all__ = [
    # Context
    "request_id_var",
    "get_request_id",
    "set_request_id",
    
    # Metrics
    "metrics",
    "MetricsCollector",
    
    # Decorators
    "track_performance",
    "track_llm_call",
    
    # Logging
    "configure_logging",
    "CustomJsonFormatter",
    "RequestIdFilter",
    
    # Cost calculation
    "calculate_llm_cost",
    "calculate_embedding_cost",
    "get_model_pricing",
]
