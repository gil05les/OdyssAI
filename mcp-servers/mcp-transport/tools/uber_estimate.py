"""
Uber estimate tool for getting ride price and time estimates.

NOTE: Uber API integration is currently disabled as we were unable to obtain
an Uber API key. This tool always returns a graceful error that triggers
LLM fallback for generating ride estimates.
"""
from uber_client import UberClient
from logger import get_logger

logger = get_logger("get_uber_estimate")


def get_uber_estimate(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    client: UberClient = None
) -> dict:
    """
    Get Uber ride price and time estimates.
    
    Args:
        origin_latitude: Starting latitude
        origin_longitude: Starting longitude
        destination_latitude: Destination latitude
        destination_longitude: Destination longitude
        client: Optional UberClient instance
    
    Returns:
        Dict with success, data/error, and source fields
    """
    if client is None:
        client = UberClient()
    
    logger.info(f"Getting Uber estimate: ({origin_latitude}, {origin_longitude}) -> ({destination_latitude}, {destination_longitude})")
    
    result = client.get_estimate(
        origin_latitude,
        origin_longitude,
        destination_latitude,
        destination_longitude
    )
    
    if result.get("success"):
        data = result.get("data", {})
        logger.info(f"Uber estimate: {data.get('price_range')}, {data.get('duration_estimate_seconds')}s")
    else:
        logger.warning(f"Uber estimate failed: {result.get('error')}")
    
    return result

