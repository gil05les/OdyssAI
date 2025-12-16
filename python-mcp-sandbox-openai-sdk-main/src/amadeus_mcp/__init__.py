"""
Amadeus MCP helper package.

Provides domain-specific helper classes that wrap the official Amadeus
Python SDK with thin, MCP-friendly tool methods. Each domain (air, hotels,
transfers, content) exposes a server class with a consistent interface.
"""

from .client import AmadeusClientConfig, build_amadeus
from .cache import ttl_cache
from .servers_air import AirServer
from .servers_hotels import HotelServer
from .servers_transfers import TransferServer
from .servers_content import ContentServer

__all__ = [
    "AmadeusClientConfig",
    "build_amadeus",
    "ttl_cache",
    "AirServer",
    "HotelServer",
    "TransferServer",
    "ContentServer",
]








