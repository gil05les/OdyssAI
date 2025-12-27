"""
Directions tools for Google Maps API.
Provides driving, transit, and walking directions with error handling.
"""
from google_maps_client import GoogleMapsClient
from logger import get_logger

logger = get_logger("directions")


def get_directions_driving(
    origin: str,
    destination: str,
    client: GoogleMapsClient = None
) -> dict:
    """
    Get driving directions between two locations.
    
    Args:
        origin: Origin address or coordinates
        destination: Destination address or coordinates
        client: Optional GoogleMapsClient instance
    
    Returns:
        Dict with success, data/error, and source fields
    """
    if client is None:
        client = GoogleMapsClient()
    
    logger.info(f"Getting driving directions: {origin} -> {destination}")
    
    result = client.get_directions(origin, destination, mode="driving")
    
    if result.get("success"):
        data = result.get("data", {})
        logger.info(f"Driving: {data.get('duration_text')}, {data.get('distance_text')}")
    else:
        logger.warning(f"Driving directions failed: {result.get('error')}")
    
    return result


def get_directions_transit(
    origin: str,
    destination: str,
    departure_time: str = None,
    client: GoogleMapsClient = None
) -> dict:
    """
    Get public transit directions between two locations.
    
    Args:
        origin: Origin address or coordinates
        destination: Destination address or coordinates
        departure_time: Optional departure time (Unix timestamp)
        client: Optional GoogleMapsClient instance
    
    Returns:
        Dict with success, data/error, and source fields
    """
    if client is None:
        client = GoogleMapsClient()
    
    logger.info(f"Getting transit directions: {origin} -> {destination}")
    
    result = client.get_directions(origin, destination, mode="transit", departure_time=departure_time)
    
    if result.get("success"):
        data = result.get("data", {})
        logger.info(f"Transit: {data.get('duration_text')}, {data.get('distance_text')}")
    else:
        logger.warning(f"Transit directions failed: {result.get('error')}")
    
    return result


def get_directions_walking(
    origin: str,
    destination: str,
    client: GoogleMapsClient = None
) -> dict:
    """
    Get walking directions between two locations.
    
    Args:
        origin: Origin address or coordinates
        destination: Destination address or coordinates
        client: Optional GoogleMapsClient instance
    
    Returns:
        Dict with success, data/error, and source fields
    """
    if client is None:
        client = GoogleMapsClient()
    
    logger.info(f"Getting walking directions: {origin} -> {destination}")
    
    result = client.get_directions(origin, destination, mode="walking")
    
    if result.get("success"):
        data = result.get("data", {})
        logger.info(f"Walking: {data.get('duration_text')}, {data.get('distance_text')}")
    else:
        logger.warning(f"Walking directions failed: {result.get('error')}")
    
    return result

