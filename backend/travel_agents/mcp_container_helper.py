"""
Helper module for managing long-running MCP server containers.
Provides utilities to check for existing containers and connect to them.
"""
import subprocess
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def container_exists(container_name: str) -> bool:
    """Check if a Docker container exists (running or stopped)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False
        )
        exists = container_name in result.stdout
        logger.debug(f"🐳 Container '{container_name}' exists: {exists}")
        return exists
    except Exception as e:
        logger.warning(f"🐳 Failed to check if container exists: {e}")
        return False


def container_is_running(container_name: str) -> bool:
    """Check if a Docker container is currently running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False
        )
        running = container_name in result.stdout
        logger.debug(f"🐳 Container '{container_name}' running: {running}")
        return running
    except Exception as e:
        logger.warning(f"🐳 Failed to check if container is running: {e}")
        return False


def ensure_container_running(container_name: str) -> bool:
    """Ensure a container is running. Start it if it exists but is stopped."""
    logger.info(f"🐳 Ensuring container '{container_name}' is running...")
    
    if not container_exists(container_name):
        logger.warning(f"🐳 Container '{container_name}' does not exist!")
        logger.info(f"   Run 'make start-mcp-flights' to create it")
        return False
    
    if not container_is_running(container_name):
        logger.info(f"🐳 Container '{container_name}' exists but stopped, starting...")
        try:
            subprocess.run(
                ["docker", "start", container_name],
                check=True,
                capture_output=True
            )
            logger.info(f"✅ Container '{container_name}' started")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to start container: {e}")
            return False
    
    logger.info(f"✅ Container '{container_name}' is already running")
    return True

