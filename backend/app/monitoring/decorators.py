"""
Performance tracking decorators for monitoring function execution.

Provides decorators for tracking LLM calls, general performance,
and recording metrics automatically.
"""

import functools
import time
import logging
from typing import Callable, Any

from .context import get_request_id
from .metrics import metrics
from .cost_calculator import calculate_llm_cost

logger = logging.getLogger(__name__)


def track_performance(operation: str):
    """
    Decorator to track execution time of any function.
    
    Args:
        operation: Name of the operation being tracked (e.g., "clustering", "search")
        
    Usage:
        @track_performance(operation="my_operation")
        async def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                
                logger.info(
                    f"{operation}_performance",
                    extra={
                        "request_id": get_request_id(),
                        "operation": operation,
                        "duration_ms": round(duration_ms, 2),
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"{operation}_performance",
                    extra={
                        "request_id": get_request_id(),
                        "operation": operation,
                        "duration_ms": round(duration_ms, 2),
                        "success": False,
                        "error": str(e)
                    }
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                
                logger.info(
                    f"{operation}_performance",
                    extra={
                        "request_id": get_request_id(),
                        "operation": operation,
                        "duration_ms": round(duration_ms, 2),
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"{operation}_performance",
                    extra={
                        "request_id": get_request_id(),
                        "operation": operation,
                        "duration_ms": round(duration_ms, 2),
                        "success": False,
                        "error": str(e)
                    }
                )
                raise
        
        # Return the appropriate wrapper based on whether func is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_llm_call(func: Callable) -> Callable:
    """
    Decorator specifically for tracking LLM API calls.
    
    Extracts token usage, calculates cost, and records to metrics.
    Works with both generate_text and generate_with_tools methods.
    
    Usage:
        @track_llm_call
        async def generate_text(self, request):
            pass
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            
            # Extract token usage and provider info from result
            provider = getattr(result, 'provider', 'unknown')
            model = getattr(result, 'model', 'unknown')
            usage = getattr(result, 'usage', {}) or {}
            
            # Handle different provider token count formats
            if provider == "google":
                tokens_in = usage.get('promptTokenCount', 0)
                tokens_out = usage.get('candidatesTokenCount', 0)
            elif provider == "openai":
                tokens_in = usage.get('prompt_tokens', 0)
                tokens_out = usage.get('completion_tokens', 0)
            elif provider == "anthropic":
                tokens_in = usage.get('input_tokens', 0)
                tokens_out = usage.get('output_tokens', 0)
            else:
                tokens_in = usage.get('total_tokens', 0)
                tokens_out = 0
            
            # Calculate cost
            cost = calculate_llm_cost(provider, model, tokens_in, tokens_out)
            
            # Log the call
            logger.info(
                "llm_call_complete",
                extra={
                    "request_id": get_request_id(),
                    "provider": provider,
                    "model": model,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "tokens_total": tokens_in + tokens_out,
                    "cost_usd": round(cost, 6),
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            # Record to metrics
            metrics.record_llm_call(
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                duration_ms=duration_ms,
                cost=cost
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "llm_call_failed",
                extra={
                    "request_id": get_request_id(),
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e)
                }
            )
            raise
    
    return wrapper


# Import asyncio at the end to avoid circular imports
import asyncio
