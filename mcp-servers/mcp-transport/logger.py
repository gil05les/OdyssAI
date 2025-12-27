"""
Logging configuration for MCP Transport Server.
Provides structured logging with timestamps, tool names, and request IDs.
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Extract tool name from extra if available
        tool_name = getattr(record, 'tool_name', 'SERVER')
        request_id = getattr(record, 'request_id', 'N/A')
        
        # Format: [TIMESTAMP] [LEVEL] [TOOL] [REQUEST_ID] [MESSAGE]
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname
        message = record.getMessage()
        
        return f"[{timestamp}] [{level}] [{tool_name}] [REQ:{request_id}] {message}"


def setup_logger(
    name: str = "mcp_transport",
    level: int = logging.DEBUG,
    log_to_file: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure the logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to a file
        log_file: Path to log file (if log_to_file is True)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler (stderr for MCP stdio compatibility - stdout is reserved for JSON-RPC)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # File handler (optional, for debugging)
    if log_to_file:
        file_handler = logging.FileHandler(log_file or 'mcp_transport.log')
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(tool_name: str = "SERVER", request_id: str = "N/A") -> logging.Logger:
    """
    Get the logger instance with context.
    
    Args:
        tool_name: Name of the tool making the log
        request_id: Unique request identifier
    
    Returns:
        Logger instance with context
    """
    global _logger
    if _logger is None:
        _logger = setup_logger()
    
    # Create a new logger with context
    context_logger = logging.LoggerAdapter(_logger, {
        'tool_name': tool_name,
        'request_id': request_id
    })
    return context_logger

