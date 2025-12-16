"""
Autocomplete airport or city tool.
Converts city names to airport codes using local database + Amadeus API fallback.

Lookup priority:
1. Local airport database (~300 major airports) - instant, no API call
2. API response cache - cached results from previous API calls
3. Amadeus API - live lookup with automatic caching
"""
import time
from typing import Dict, Any, List, Optional
from amadeus import Location
from amadeus.client.errors import ResponseError, NetworkError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger
from .airport_cache import get_airport_database, get_api_cache


def autocomplete_airport_or_city(
    query: str,
    country_code: Optional[str] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Convert city/airport name to IATA codes.
    
    Uses a three-tier lookup strategy:
    1. Local database of major airports (instant)
    2. Cached API responses (instant)
    3. Live Amadeus API call (cached for future use)
    
    Args:
        query: City or airport name (e.g., "Zurich", "New York")
        country_code: Optional country code (e.g., "CH", "US")
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with 'locations' array containing location objects
        Each location has: iata, type, city, country
    
    Example:
        Input: {"query": "Zurich", "country_code": "CH"}
        Output: {
            "locations": [
                {"iata": "ZRH", "type": "AIRPORT", "city": "Zurich", "country": "CH"}
            ]
        }
    """
    request_id = f"autocomplete_{int(time.time() * 1000)}"
    logger = get_logger("autocomplete_airport_or_city", request_id)
    
    try:
        logger.info(f"Starting autocomplete for query: '{query}'" + 
                   (f", country: {country_code}" if country_code else ""))
        
        # === TIER 1: Local Airport Database ===
        airport_db = get_airport_database()
        local_results = airport_db.search(query, country_code)
        
        if local_results:
            logger.info(f"Local DB hit: found {len(local_results)} airports for '{query}'")
            return {'locations': local_results, 'source': 'local_db'}
        
        logger.debug(f"Local DB miss for '{query}', checking API cache...")
        
        # === TIER 2: API Response Cache ===
        api_cache = get_api_cache()
        cached_result = api_cache.get(query, country_code)
        
        if cached_result:
            logger.info(f"Cache hit: returning cached result for '{query}'")
            return cached_result
        
        logger.debug(f"Cache miss for '{query}', calling Amadeus API...")
        
        # === TIER 3: Live Amadeus API Call ===
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Build parameters
        params = {
            'keyword': query,
            'subType': Location.AIRPORT
        }
        
        if country_code:
            params['countryCode'] = country_code
        
        logger.debug(f"Calling Amadeus API: GET /v1/reference-data/locations")
        logger.debug(f"Parameters: {params}")
        
        # Add initial delay to allow sandbox network rules to be set up
        initial_delay = 2.0
        logger.debug(f"Waiting {initial_delay}s for sandbox network setup...")
        time.sleep(initial_delay)
        
        start_time = time.time()
        
        # Make the API call with retry logic for NetworkError
        max_retries = 5
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                response = amadeus.reference_data.locations.get(**params)
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
        
        # Normalize response
        locations = []
        if response.data:
            for location in response.data:
                normalized = {
                    'iata': location.get('iataCode', ''),
                    'type': location.get('subType', ''),
                    'city': location.get('address', {}).get('cityName', ''),
                    'country': location.get('address', {}).get('countryCode', '')
                }
                locations.append(normalized)
                logger.debug(f"Found location: {normalized}")
        
        logger.info(f"Found {len(locations)} locations from API")
        
        # Cache the result for future use
        result = {'locations': locations, 'source': 'api'}
        api_cache.set(query, country_code, result)
        logger.debug(f"Cached result for '{query}'")
        
        return result
        
    except NetworkError as error:
        # NetworkError is a specific Amadeus error for network issues
        # This happens when the MCP sandbox blocks network access
        # Return empty results instead of crashing - the LLM can still function
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        logger.warning(f"Network error connecting to Amadeus API: {error_desc}")
        logger.warning(f"Returning empty results for '{query}' - city not in local database and API unavailable")
        return {'locations': [], 'source': 'network_error', 'error': f"City '{query}' not found in local database and API unavailable"}
        
    except ResponseError as error:
        error_type = type(error).__name__
        error_code = getattr(error, 'code', None)
        # description is a METHOD, not a property - call it!
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        
        # For rate limit errors, return empty results gracefully
        if error_code == 429:
            logger.warning(f"Rate limited by Amadeus API for query '{query}'")
            return {'locations': [], 'source': 'rate_limited', 'error': 'API rate limit exceeded'}
        
        logger.error(f"Amadeus API error: {error_type} (code={error_code}): {error_desc}")
        raise Exception(f"Failed to autocomplete locations: {error_type} (code={error_code}) - {error_desc}")
        
    except Exception as error:
        error_str = str(error)
        error_type = type(error).__name__
        
        logger.error(f"Unexpected error: {error_type}: {error_str}", exc_info=True)
        raise Exception(f"Failed to autocomplete locations: {error_type}: {error_str}")
