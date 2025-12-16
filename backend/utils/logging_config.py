"""
Comprehensive logging configuration for OdyssAI backend.

Provides detailed logging to both files and console, with separate log files for:
- General application logs
- Agent execution logs (input/output, state transitions)
- MCP server communication logs
- API request/response logs
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler

# Determine project root and logs directory
# In Docker: /app/backend/utils/logging_config.py -> /app/logs
# Locally: backend/utils/logging_config.py -> OdyssAI/logs
_backend_dir = Path(__file__).parent.parent

# Check if we're in Docker (backend is at /app/backend)
if str(_backend_dir).startswith('/app'):
    # Docker environment: logs at /app/logs
    _logs_dir = Path('/app/logs')
else:
    # Local environment: logs at project root
    _project_root = _backend_dir.parent
    _logs_dir = _project_root / 'logs'

# Create logs directory if it doesn't exist
_logs_dir.mkdir(exist_ok=True)

# Log file paths
APP_LOG_FILE = _logs_dir / 'app.log'
AGENT_LOG_FILE = _logs_dir / 'agents.log'
MCP_LOG_FILE = _logs_dir / 'mcp.log'
API_LOG_FILE = _logs_dir / 'api.log'
ERROR_LOG_FILE = _logs_dir / 'errors.log'

# Detailed formatter with more context
DETAILED_FORMATTER = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(lineno)-4d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Simple formatter for console
CONSOLE_FORMATTER = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
    datefmt='%H:%M:%S'
)


def setup_logging(
    level: int = logging.DEBUG,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        level: Logging level (default: DEBUG for maximum detail)
        enable_file_logging: Whether to log to files
        enable_console_logging: Whether to log to console
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    if enable_file_logging:
        # Application log (general)
        app_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(level)
        app_handler.setFormatter(DETAILED_FORMATTER)
        root_logger.addHandler(app_handler)
        
        # Agent execution log (detailed agent I/O)
        agent_handler = RotatingFileHandler(
            AGENT_LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        agent_handler.setLevel(logging.DEBUG)
        agent_handler.setFormatter(DETAILED_FORMATTER)
        agent_logger = logging.getLogger('agents')
        agent_logger.addHandler(agent_handler)
        agent_logger.setLevel(logging.DEBUG)
        agent_logger.propagate = False
        
        # MCP server log (MCP communication)
        mcp_handler = RotatingFileHandler(
            MCP_LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        mcp_handler.setLevel(logging.DEBUG)
        mcp_handler.setFormatter(DETAILED_FORMATTER)
        mcp_logger = logging.getLogger('mcp')
        mcp_logger.addHandler(mcp_handler)
        mcp_logger.setLevel(logging.DEBUG)
        mcp_logger.propagate = False
        
        # API log (request/response)
        api_handler = RotatingFileHandler(
            API_LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(DETAILED_FORMATTER)
        api_logger = logging.getLogger('api')
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.DEBUG)
        api_logger.propagate = False
        
        # Error log (errors only)
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(DETAILED_FORMATTER)
        root_logger.addHandler(error_handler)
    
    if enable_console_logging:
        # Console handler (always enabled)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(CONSOLE_FORMATTER)
        root_logger.addHandler(console_handler)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("🚀 OdyssAI Logging System Initialized")
    logger.info("=" * 80)
    logger.info(f"📁 Log directory: {_logs_dir}")
    if enable_file_logging:
        logger.info(f"📄 Application log: {APP_LOG_FILE}")
        logger.info(f"📄 Agent log: {AGENT_LOG_FILE}")
        logger.info(f"📄 MCP log: {MCP_LOG_FILE}")
        logger.info(f"📄 API log: {API_LOG_FILE}")
        logger.info(f"📄 Error log: {ERROR_LOG_FILE}")
    logger.info(f"🔍 Log level: {logging.getLevelName(level)}")
    logger.info("=" * 80)


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger for a specific agent with detailed logging capabilities."""
    logger = logging.getLogger(f'agents.{agent_name}')
    return logger


def get_mcp_logger(server_name: str) -> logging.Logger:
    """Get a logger for a specific MCP server with detailed logging capabilities."""
    logger = logging.getLogger(f'mcp.{server_name}')
    return logger


def get_api_logger() -> logging.Logger:
    """Get a logger for API requests/responses."""
    return logging.getLogger('api')


def log_agent_input(logger: logging.Logger, agent_name: str, method: str, input_data: Dict[str, Any]) -> None:
    """Log agent input with detailed formatting."""
    logger.debug("=" * 80)
    logger.debug(f"📥 AGENT INPUT: {agent_name}.{method}")
    logger.debug("=" * 80)
    logger.debug(f"Agent: {agent_name}")
    logger.debug(f"Method: {method}")
    logger.debug(f"Input Data:\n{json.dumps(input_data, indent=2, default=str)}")
    logger.debug("=" * 80)


def log_agent_output(logger: logging.Logger, agent_name: str, method: str, output_data: Any, success: bool = True) -> None:
    """Log agent output with detailed formatting."""
    status = "✅ SUCCESS" if success else "❌ FAILURE"
    logger.debug("=" * 80)
    logger.debug(f"📤 AGENT OUTPUT: {agent_name}.{method} - {status}")
    logger.debug("=" * 80)
    logger.debug(f"Agent: {agent_name}")
    logger.debug(f"Method: {method}")
    logger.debug(f"Success: {success}")
    
    if isinstance(output_data, dict):
        logger.debug(f"Output Data:\n{json.dumps(output_data, indent=2, default=str)}")
    elif hasattr(output_data, 'model_dump'):
        logger.debug(f"Output Data:\n{json.dumps(output_data.model_dump(), indent=2, default=str)}")
    else:
        logger.debug(f"Output Data: {output_data}")
    
    logger.debug("=" * 80)


def log_agent_state(logger: logging.Logger, agent_name: str, state: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log agent state transition."""
    logger.info(f"🔄 STATE: {agent_name} -> {state}")
    if details:
        logger.debug(f"State Details:\n{json.dumps(details, indent=2, default=str)}")


def log_mcp_request(logger: logging.Logger, server_name: str, tool_name: str, request_data: Dict[str, Any]) -> None:
    """Log MCP tool request."""
    logger.debug("=" * 80)
    logger.debug(f"📡 MCP REQUEST: {server_name}.{tool_name}")
    logger.debug("=" * 80)
    logger.debug(f"Server: {server_name}")
    logger.debug(f"Tool: {tool_name}")
    logger.debug(f"Request:\n{json.dumps(request_data, indent=2, default=str)}")
    logger.debug("=" * 80)


def log_mcp_response(logger: logging.Logger, server_name: str, tool_name: str, response_data: Any, success: bool = True) -> None:
    """Log MCP tool response."""
    status = "✅ SUCCESS" if success else "❌ FAILURE"
    logger.debug("=" * 80)
    logger.debug(f"📥 MCP RESPONSE: {server_name}.{tool_name} - {status}")
    logger.debug("=" * 80)
    logger.debug(f"Server: {server_name}")
    logger.debug(f"Tool: {tool_name}")
    logger.debug(f"Success: {success}")
    
    if isinstance(response_data, dict):
        logger.debug(f"Response:\n{json.dumps(response_data, indent=2, default=str)}")
    else:
        logger.debug(f"Response: {response_data}")
    
    logger.debug("=" * 80)


def log_api_request(logger: logging.Logger, method: str, path: str, headers: Dict[str, str], body: Optional[Any] = None) -> None:
    """Log API request."""
    logger.info("=" * 80)
    logger.info(f"🌐 API REQUEST: {method} {path}")
    logger.info("=" * 80)
    logger.debug(f"Method: {method}")
    logger.debug(f"Path: {path}")
    logger.debug(f"Headers: {json.dumps(dict(headers), indent=2)}")
    if body:
        if isinstance(body, dict):
            logger.debug(f"Body:\n{json.dumps(body, indent=2, default=str)}")
        else:
            logger.debug(f"Body: {body}")
    logger.info("=" * 80)


def log_api_response(logger: logging.Logger, method: str, path: str, status_code: int, response_data: Optional[Any] = None, duration: Optional[float] = None) -> None:
    """Log API response."""
    status_emoji = "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "⚠️"
    logger.info("=" * 80)
    logger.info(f"{status_emoji} API RESPONSE: {method} {path} - {status_code}")
    logger.info("=" * 80)
    logger.info(f"Method: {method}")
    logger.info(f"Path: {path}")
    logger.info(f"Status: {status_code}")
    if duration is not None:
        logger.info(f"Duration: {duration:.3f}s")
    if response_data:
        if isinstance(response_data, dict):
            logger.debug(f"Response:\n{json.dumps(response_data, indent=2, default=str)}")
        else:
            logger.debug(f"Response: {response_data}")
    logger.info("=" * 80)


# Initialize logging on import
setup_logging(
    level=logging.DEBUG,
    enable_file_logging=True,
    enable_console_logging=True
)

