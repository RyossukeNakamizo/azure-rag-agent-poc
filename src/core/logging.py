"""
Structured Logging Configuration with structlog
"""

import logging
import os
import sys
from typing import Any, Dict
import structlog
from structlog.typing import EventDict, WrappedLogger


def add_app_context(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log events."""
    event_dict["app"] = "azure-rag-agent"
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    enable_colors: bool = False
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Output logs as JSON (recommended for production)
        enable_colors: Enable colored console output (development only)
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Structlog processors pipeline
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]
    
    if json_logs:
        # Production: JSON output
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Human-readable output
        processors.append(structlog.dev.ConsoleRenderer(colors=enable_colors))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Application Insights integration placeholder
class ApplicationInsightsHandler(logging.Handler):
    """
    Custom handler for Azure Application Insights.
    
    Future enhancement: Send logs to Application Insights
    """
    
    def __init__(self, connection_string: str = None):
        super().__init__()
        self.connection_string = connection_string
        # TODO: Initialize Application Insights client
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to Application Insights."""
        # TODO: Implement Application Insights integration
        pass
