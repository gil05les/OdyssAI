"""
Geocoding tool for converting addresses to coordinates.
"""
from google_maps_client import GoogleMapsClient
from logger import get_logger

logger = get_logger("geocode_location")


def geocode_location(address: str, client: GoogleMapsClient = None) -> dict:
    """
    Geocode an address or place name to get coordinates.
    
    Args:
        address: Address or place name to geocode
        client: Optional GoogleMapsClient instance
    
    Returns:
        Dict with success, data/error, and source fields
    """
    if client is None:
        client = GoogleMapsClient()
    
    logger.info(f"Geocoding address: {address}")
    
    result = client.geocode(address)
    
    if result.get("success"):
        logger.info(f"Successfully geocoded '{address}'")
    else:
        logger.warning(f"Geocoding failed for '{address}': {result.get('error')}")
    
    return result

