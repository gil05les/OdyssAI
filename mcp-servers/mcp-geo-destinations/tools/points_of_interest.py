"""
Get points of interest tool.
Retrieves POIs from Amadeus API for a specific location.
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from amadeus.client.errors import ResponseError

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    current_file = Path(__file__).resolve()
    env_path = current_file.parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except (ImportError, NameError):
    pass

from logger import get_logger

# Import Amadeus client wrapper (reuse from mcp-flights pattern)
try:
    # Try to import from a shared location or create inline
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'mcp-flights'))
    from amadeus_client import AmadeusClientWrapper
except ImportError:
    # Fallback: create a simple wrapper
    from amadeus import Client
    class AmadeusClientWrapper:
        def __init__(self):
            client_id = os.getenv('AMADEUS_CLIENT_ID') or os.getenv('AMADEUS_API_KEY')
            client_secret = os.getenv('AMADEUS_CLIENT_SECRET') or os.getenv('AMADEUS_API_SECRET')
            hostname = os.getenv('AMADEUS_HOSTNAME', os.getenv('AMADEUS_ENV', 'test'))
            if hostname == 'prod':
                hostname = 'production'
            self.client = Client(client_id=client_id, client_secret=client_secret, hostname=hostname)
        def get_client(self):
            return self.client


def get_points_of_interest(
    latitude: float,
    longitude: float,
    radius: Optional[float] = None,
    radius_unit: str = "KM",
    categories: Optional[List[str]] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Get points of interest near a specific location.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius: Optional search radius (default: API default, typically 2km)
        radius_unit: Unit for radius - "KM" or "MILE" (default: "KM")
        categories: Optional list of POI categories to filter
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with points of interest
    
    Example:
        Input: {
            "latitude": 38.7223,
            "longitude": -9.1393,
            "radius": 5.0
        }
        Output: {
            "pois": [...],
            "total_pois": 10
        }
    """
    request_id = f"pois_{int(time.time() * 1000)}"
    logger = get_logger("get_points_of_interest", request_id)
    
    try:
        logger.info(
            f"Fetching POIs near coordinates: ({latitude}, {longitude})" +
            (f" within {radius} {radius_unit}" if radius else "")
        )
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Build parameters for POI search
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        
        if radius:
            params['radius'] = radius
        if radius_unit:
            params['radiusUnit'] = radius_unit
        if categories:
            params['categories'] = ','.join(categories)
        
        logger.debug(f"Calling Amadeus API: GET /v1/reference-data/locations/pois")
        logger.debug(f"Parameters: {params}")
        
        start_time = time.time()
        
        # Call Amadeus API
        # The POIs endpoint might be under reference_data.locations
        try:
            # Try the reference_data.locations.pois endpoint
            response = amadeus.reference_data.locations.pois.get(**params)
        except AttributeError:
            # Fallback to generic get method
            try:
                response = amadeus.get('/v1/reference-data/locations/pois', params=params)
            except Exception as e:
                logger.error(f"Failed to access POIs endpoint: {e}")
                raise Exception(
                    f"Unable to access POIs endpoint: {e}. "
                    "This endpoint may not be available in the Amadeus Python SDK or test environment."
                )
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s")
        
        # Normalize response
        pois = []
        if response.data:
            for poi in response.data:
                normalized_poi = {
                    'poi_id': poi.get('id', ''),
                    'name': poi.get('name', ''),
                    'category': poi.get('category', ''),
                    'subcategory': poi.get('subcategory', ''),
                    'geo_code': {
                        'latitude': poi.get('geoCode', {}).get('latitude', 0),
                        'longitude': poi.get('geoCode', {}).get('longitude', 0)
                    },
                    'address': {
                        'city_name': poi.get('address', {}).get('cityName', ''),
                        'country_code': poi.get('address', {}).get('countryCode', ''),
                        'region_code': poi.get('address', {}).get('regionCode', ''),
                        'postal_code': poi.get('address', {}).get('postalCode', ''),
                        'street': poi.get('address', {}).get('lines', [''])[0] if poi.get('address', {}).get('lines') else ''
                    },
                    'distance': poi.get('distance', {}).get('value', 0) if poi.get('distance') else 0,
                    'distance_unit': poi.get('distance', {}).get('unit', 'KM') if poi.get('distance') else 'KM',
                    'tags': poi.get('tags', [])
                }
                pois.append(normalized_poi)
                logger.debug(f"Found POI: {normalized_poi['name']} ({normalized_poi['category']})")
        
        logger.info(f"Found {len(pois)} points of interest")
        
        # Group by category
        by_category = {}
        for poi in pois:
            category = poi.get('category', 'UNKNOWN')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(poi)
        
        return {
            'pois': pois,
            'total_pois': len(pois),
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            },
            'radius': radius,
            'radius_unit': radius_unit,
            'by_category': by_category
        }
        
    except ResponseError as error:
        error_msg = str(error)
        error_code = getattr(error, 'code', None)
        
        if error_code == 404:
            error_msg += (
                " POIs endpoint may not be available in test environment. "
                "This endpoint might require production credentials or may not be available in your Amadeus plan."
            )
        
        logger.error(f"Amadeus API error: {error_msg}")
        raise Exception(f"Failed to get points of interest: {error_msg}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to get points of interest: {str(error)}")






