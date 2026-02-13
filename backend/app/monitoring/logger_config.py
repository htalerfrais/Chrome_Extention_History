"""
Structured logging configuration using python-json-logger.

Configures JSON-formatted logging with automatic request_id injection
for better traceability across service boundaries.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from .context import get_request_id


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that automatically injects request_id
    from context into every log record.
    """
    
    def add_fields(self, log_record, record, message_dict):
        """
        Add custom fields to the log record.
        
        Args:
            log_record: The dictionary that will be logged as JSON
            record: The LogRecord object
            message_dict: Dictionary of message and extra fields
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add request_id from context
        log_record['request_id'] = get_request_id()
        
        # Add timestamp
        log_record['timestamp'] = self.formatTime(record)
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add level name
        log_record['level'] = record.levelname


def configure_logging(
    log_level: str = "INFO",
    use_json: bool = True
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: If True, use JSON format; otherwise use plain text
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if use_json:
        # Use JSON formatter
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Use plain text formatter with request_id
        formatter = logging.Formatter(
            '[%(levelname)s] [%(name)s] [req:%(request_id)s] %(message)s'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))


# Filter to add request_id to plain text logs
class RequestIdFilter(logging.Filter):
    """Filter that adds request_id to log records."""
    
    def filter(self, record):
        record.request_id = get_request_id()
        return True
