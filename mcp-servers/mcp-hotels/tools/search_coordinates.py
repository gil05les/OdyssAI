"""
Search hotels by coordinates tool.
Finds hotels near a specific location using geocode.
"""
import time
from typing import Dict, Any, Optional
from amadeus.client.errors import ResponseError, NetworkError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger


def search_hotels_by_coordinates(
    latitude: float,
    longitude: float,
    radius: Optional[float] = None,
    radius_unit: str = "KM",
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
    guests: int = 1,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Search for hotels by geographic coordinates.
    
    Args:
        latitude: Latitude coordinate (e.g., 38.7223)
        longitude: Longitude coordinate (e.g., -9.1393)
        radius: Optional search radius (default: API default)
        radius_unit: Unit for radius - "KM" or "MILE" (default: "KM")
        check_in: Optional check-in date in YYYY-MM-DD format
        check_out: Optional check-out date in YYYY-MM-DD format
        guests: Number of guests (default: 1)
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with hotel information
    
    Example:
        Input: {
            "latitude": 38.7223,
            "longitude": -9.1393,
            "radius": 5.0,
            "check_in": "2025-05-10",
            "check_out": "2025-05-17",
            "guests": 2
        }
        Output: {
            "hotels": [...],
            "total_hotels": 10
        }
    """
    request_id = f"search_coords_{int(time.time() * 1000)}"
    logger = get_logger("search_hotels_by_coordinates", request_id)
    
    try:
        logger.info(
            f"Searching hotels near coordinates: ({latitude}, {longitude})" +
            (f" within {radius} {radius_unit}" if radius else "")
        )
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Build parameters for geocode search
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        
        if radius:
            params['radius'] = radius
        if radius_unit:
            params['radiusUnit'] = radius_unit
        
        logger.debug(f"Calling Amadeus API: GET /v1/reference-data/locations/hotels/by-geocode")
        logger.debug(f"Parameters: {params}")
        
        start_time = time.time()
        
        # Add initial delay to allow sandbox network rules to be set up
        initial_delay = 2.0  # 2 seconds for network setup
        logger.debug(f"Waiting {initial_delay}s for sandbox network setup...")
        time.sleep(initial_delay)
        
        # Call Amadeus API with retry logic for NetworkError
        # NetworkError can occur when sandbox network rules aren't ready yet
        max_retries = 5
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                # Call Amadeus API
                response = amadeus.reference_data.locations.hotels.by_geocode.get(**params)
                break  # Success, exit retry loop
            except NetworkError as error:
                retry_count += 1
                error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
                logger.warning(f"Network error (attempt {retry_count}/{max_retries + 1}): {error_desc}")
                
                if retry_count <= max_retries:
                    # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                    delay = 2.0 * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {delay:.1f}s (sandbox network may still be initializing)...")
                    time.sleep(delay)
                else:
                    # Max retries reached, re-raise to be caught by outer handler
                    raise
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s (after {retry_count} retries)")
        
        # Normalize response
        hotels = []
        if response.data:
            for hotel in response.data:
                normalized_hotel = {
                    'hotel_id': hotel.get('hotelId', ''),
                    'name': hotel.get('name', ''),
                    'iata_code': hotel.get('iataCode', ''),
                    'geo_code': {
                        'latitude': hotel.get('geoCode', {}).get('latitude', 0),
                        'longitude': hotel.get('geoCode', {}).get('longitude', 0)
                    },
                    'address': {
                        'city_name': hotel.get('address', {}).get('cityName', ''),
                        'country_code': hotel.get('address', {}).get('countryCode', ''),
                        'region_code': hotel.get('address', {}).get('regionCode', '')
                    },
                    'distance': hotel.get('distance', {}).get('value', 0) if hotel.get('distance') else 0,
                    'distance_unit': hotel.get('distance', {}).get('unit', 'KM') if hotel.get('distance') else 'KM'
                }
                hotels.append(normalized_hotel)
                logger.debug(f"Found hotel: {normalized_hotel['name']}")
        
        logger.info(f"Found {len(hotels)} hotels")
        
        # If check-in/check-out dates are provided, get offers for these hotels
        offers_info = None
        if check_in and check_out and hotels:
            logger.info("Fetching hotel offers for specified dates...")
            try:
                # Get offers for the first few hotels (limit to avoid too many API calls)
                hotel_ids = [h['hotel_id'] for h in hotels[:20] if h['hotel_id']]
                
                if hotel_ids:
                    offers_params = {
                        'hotelIds': ','.join(hotel_ids),
                        'checkInDate': check_in,
                        'checkOutDate': check_out,
                        'adults': guests
                    }
                    
                    # Call hotel offers API with retry logic for NetworkError
                    retry_count_offers = 0
                    offers_response = None
                    
                    while retry_count_offers <= max_retries:
                        try:
                            offers_response = amadeus.shopping.hotel_offers_search.get(**offers_params)
                            break  # Success, exit retry loop
                        except NetworkError as error:
                            retry_count_offers += 1
                            error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
                            logger.warning(f"Network error on hotel offers (attempt {retry_count_offers}/{max_retries + 1}): {error_desc}")
                            
                            if retry_count_offers <= max_retries:
                                # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                                delay = 2.0 * (2 ** (retry_count_offers - 1))
                                logger.info(f"Retrying hotel offers in {delay:.1f}s (sandbox network may still be initializing)...")
                                time.sleep(delay)
                            else:
                                # Max retries reached, skip offers but don't fail the whole request
                                logger.warning("Max retries reached for hotel offers, continuing without offers")
                                offers_response = None
                                break
                    
                    if offers_response.data:
                        offers_info = {
                            'total_offers': sum(len(h.get('offers', [])) for h in offers_response.data),
                            'hotels_with_offers': len(offers_response.data)
                        }
                        logger.info(f"Found offers for {offers_info['hotels_with_offers']} hotels")
            except Exception as e:
                logger.warning(f"Could not fetch offers: {e}")
        
        return {
            'hotels': hotels,
            'total_hotels': len(hotels),
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            },
            'radius': radius,
            'radius_unit': radius_unit,
            'offers_info': offers_info
        }
        
    except NetworkError as error:
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        logger.error(f"Network error after retries: {error_desc}")
        raise Exception(f"Failed to search hotels: Network error - {error_desc}")
    except ResponseError as error:
        error_msg = str(error) if hasattr(error, '__str__') else f"Error code: {getattr(error, 'code', 'unknown')}"
        logger.error(f"Amadeus API error: {error_msg}")
        raise Exception(f"Failed to search hotels by coordinates: {error_msg}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to search hotels by coordinates: {str(error)}")

