"""
Context management for request tracing using Python's contextvars.

This module provides a contextvars-based approach to propagate request_id
through the entire async call chain without parameter passing.
"""
import contextvars

# Context variable for request ID - automatically propagates through async calls
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", 
    default="no-request"
)

def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()

def set_request_id(request_id: str) -> None:
    """Set the request ID in context."""
    request_id_var.set(request_id)
