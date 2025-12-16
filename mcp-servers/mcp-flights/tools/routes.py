"""
Get airline routes tool.
Retrieves destinations served by an airline from a specific origin.
"""
import time
from typing import Dict, Any, List, Optional
from amadeus.client.errors import ResponseError, NetworkError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger
from .airport_cache import get_routes_cache


def get_airline_routes(
    airline_code: str,
    origin: Optional[str] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Get destinations served by an airline from a specific origin.
    
    Args:
        airline_code: IATA airline code (e.g., "LX" for Swiss)
        origin: Optional origin airport code (e.g., "ZRH")
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with airline routes information
    
    Example:
        Input: {"airline_code": "LX", "origin": "ZRH"}
        Output: {
            "airline": "LX",
            "origin": "ZRH",
            "destinations": ["LIS", "BCN", "PAR", ...]
        }
    """
    request_id = f"routes_{int(time.time() * 1000)}"
    logger = get_logger("get_airline_routes", request_id)
    
    try:
        logger.info(f"Getting routes for airline: {airline_code}" +
                   (f" from origin: {origin}" if origin else ""))
        
        # === Check cache first ===
        routes_cache = get_routes_cache()
        cached_result = routes_cache.get(airline_code, origin)
        
        if cached_result:
            logger.info(f"Cache hit: returning cached airline routes")
            return cached_result
        
        logger.debug(f"Cache miss for airline routes, calling Amadeus API...")
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Use airline.destinations endpoint to get all destinations for the airline
        logger.debug(f"Calling Amadeus API: GET /v1/airline/destinations")
        params = {'airlineCode': airline_code}
        logger.debug(f"Parameters: {params}")
        
        # Add initial delay to allow sandbox network rules to be set up
        initial_delay = 2.0
        logger.debug(f"Waiting {initial_delay}s for sandbox network setup...")
        time.sleep(initial_delay)
        
        start_time = time.time()
        
        # Call airline destinations API with retry logic for NetworkError
        max_retries = 5
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                response = amadeus.airline.destinations.get(**params)
                break  # Success, exit retry loop
            except NetworkError as error:
                retry_count += 1
                error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
                logger.warning(f"Network error (attempt {retry_count}/{max_retries + 1}): {error_desc}")
                
                if retry_count <= max_retries:
                    delay = 2.0 * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {delay:.1f}s (sandbox network may still be initializing)...")
                    time.sleep(delay)
                else:
                    raise
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s (after {retry_count} retries)")
        
        # Extract destinations
        destinations = []
        response_data = response.data if hasattr(response, 'data') else []
        
        if response_data:
            for dest in response_data:
                # Extract IATA code from destination
                dest_code = dest.get('iataCode', '')
                if dest_code:
                    destinations.append(dest_code)
                    logger.debug(f"Found destination: {dest_code}")
        
        # If origin is specified, note that we're returning all destinations for the airline
        # The API doesn't filter by origin, but the agent can use search_flights to verify
        # if the airline serves a specific origin-destination route
        if origin:
            logger.info(
                f"Returning all destinations for airline {airline_code}. "
                f"To verify routes from {origin}, use search_flights with origin={origin} and filter by airline."
            )
        
        logger.info(f"Found {len(destinations)} destinations")
        
        result = {
            'airline': airline_code,
            'origin': origin,
            'destinations': destinations,
            'total_destinations': len(destinations),
            'source': 'api'
        }
        
        # Cache the result
        routes_cache.set(airline_code, origin, result)
        logger.debug(f"Cached airline routes result")
        
        return result
        
    except NetworkError as error:
        # NetworkError is a specific Amadeus error for network issues
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        logger.warning(f"Network error connecting to Amadeus API: {error_desc}")
        logger.warning(f"Returning empty results for airline {airline_code} - API unavailable")
        return {
            'airline': airline_code,
            'origin': origin,
            'destinations': [],
            'total_destinations': 0,
            'source': 'network_error',
            'error': 'API unavailable'
        }
    except ResponseError as error:
        error_type = type(error).__name__
        error_code = getattr(error, 'code', None)
        # description is a METHOD, not a property - call it!
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        
        # For rate limit errors, return empty results gracefully
        if error_code == 429:
            logger.warning(f"Rate limited by Amadeus API for airline routes {airline_code}")
            return {
                'airline': airline_code,
                'origin': origin,
                'destinations': [],
                'total_destinations': 0,
                'source': 'rate_limited',
                'error': 'API rate limit exceeded'
            }
        
        logger.error(f"Amadeus API error: {error_type} (code={error_code}): {error_desc}")
        raise Exception(f"Failed to get airline routes: {error_type} (code={error_code}) - {error_desc}")
    except Exception as error:
        error_str = str(error)
        error_type = type(error).__name__
        
        logger.error(f"Unexpected error: {error_type}: {error_str}", exc_info=True)
        raise Exception(f"Failed to get airline routes: {error_type}: {error_str}")

