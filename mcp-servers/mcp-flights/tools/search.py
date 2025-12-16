"""
Search flights tool.
Finds available flights between origin and destination using Amadeus Flight Offers Search API.
"""
import time
import json
from typing import Dict, Any, List, Optional
from amadeus.client.errors import ResponseError, NetworkError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger
from .airport_cache import get_flight_search_cache


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    max_price: Optional[float] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Search for available flights.
    
    Args:
        origin: Origin airport code (e.g., "ZRH")
        destination: Destination airport code (e.g., "LIS")
        departure_date: Departure date in YYYY-MM-DD format (e.g., "2025-05-10")
        return_date: Optional return date in YYYY-MM-DD format (e.g., "2025-05-17")
        adults: Number of adult passengers (default: 1)
        max_price: Optional maximum price filter
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with 'flight_options' array containing normalized flight offers
        Each flight has: id, price, currency, segments, airlines, flight_number, return_flight_number (if round trip),
        return_departure_time, return_arrival_time, return_departure_airport, return_arrival_airport
    
    Example:
        Input: {
            "origin": "ZRH",
            "destination": "LIS",
            "departure_date": "2025-05-10",
            "return_date": "2025-05-17",
            "adults": 1,
            "max_price": 1000
        }
        Output: {
            "flight_options": [
                {
                    "id": "OFFER_123",
                    "price": 420,
                    "currency": "CHF",
                    "segments": [...],
                    "airlines": ["LX", "TP"]
                }
            ]
        }
    """
    request_id = f"search_{int(time.time() * 1000)}"
    logger = get_logger("search_flights", request_id)
    
    try:
        logger.info("=" * 80)
        logger.info(f"=== TOOL: search_flights ===")
        logger.info("=" * 80)
        logger.info(f"Request ID: {request_id}")
        logger.info(f"Full Input Parameters:")
        logger.info(f"  origin: {origin}")
        logger.info(f"  destination: {destination}")
        logger.info(f"  departure_date: {departure_date}")
        logger.info(f"  return_date: {return_date}")
        logger.info(f"  adults: {adults}")
        logger.info(f"  max_price: {max_price}")
        logger.info("=" * 80)
        
        # === Check cache first ===
        search_cache = get_flight_search_cache()
        cached_result = search_cache.get(origin, destination, departure_date, return_date, adults)
        
        if cached_result:
            logger.info(f"Cache hit: returning cached flight search results")
            # Apply max_price filter to cached results if specified
            if max_price:
                filtered_options = [
                    opt for opt in cached_result.get('flight_options', [])
                    if opt.get('price', float('inf')) <= max_price
                ]
                cached_result = cached_result.copy()
                cached_result['flight_options'] = filtered_options
                logger.debug(f"Filtered cached results: {len(filtered_options)} options after max_price filter")
            return cached_result
        
        logger.debug(f"Cache miss for flight search, calling Amadeus API...")
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Build parameters
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults
        }
        
        if return_date:
            params['returnDate'] = return_date
        
        logger.info(f"=== AMADEUS API REQUEST ===")
        logger.info(f"Endpoint: GET /v2/shopping/flight-offers")
        logger.info(f"Full Request Parameters: {json.dumps(params, indent=2, default=str)}")
        
        # Add initial delay to allow sandbox network rules to be set up
        # This is especially important when a new container is created
        initial_delay = 2.0  # 2 seconds for network setup
        logger.debug(f"Waiting {initial_delay}s for sandbox network setup...")
        time.sleep(initial_delay)
        
        start_time = time.time()
        
        # Call Amadeus API with retry logic for NetworkError
        # NetworkError can occur when sandbox network rules aren't ready yet
        max_retries = 5
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                response = amadeus.shopping.flight_offers_search.get(**params)
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
        logger.info(f"=== AMADEUS API RESPONSE ===")
        
        # Log full API response for debugging
        if response.data:
            logger.info(f"Response: {len(response.data)} flight offers returned")
            # Log full response data
            logger.debug(f"Full API Response Data: {json.dumps(response.data, indent=2, default=str)}")
        else:
            logger.warning(f"API Response: No data returned")
        
        # Normalize response
        flight_options = []
        if response.data:
            for offer in response.data:
                # Extract price
                price_info = offer.get('price', {})
                total_price = float(price_info.get('total', 0))
                currency = price_info.get('currency', 'CHF')
                
                # Apply max_price filter if specified
                if max_price and total_price > max_price:
                    logger.debug(f"Skipping offer {offer.get('id')} - price {total_price} exceeds max {max_price}")
                    continue
                
                # Extract segments and format flight numbers
                segments = []
                itineraries = offer.get('itineraries', [])
                outbound_flight_number = None
                return_flight_number = None
                return_departure_time = None
                return_arrival_time = None
                return_departure_airport = None
                return_arrival_airport = None
                
                for itinerary_idx, itinerary in enumerate(itineraries):
                    itinerary_segments = itinerary.get('segments', [])
                    for seg_idx, segment in enumerate(itinerary_segments):
                        carrier_code = segment.get('carrierCode', '')
                        segment_number = segment.get('number', '')
                        # Format flight number: carrierCode + number (e.g., "KL1005")
                        flight_number = f"{carrier_code}{segment_number}" if carrier_code and segment_number else None
                        
                        departure = segment.get('departure', {})
                        arrival = segment.get('arrival', {})
                        
                        segments.append({
                            'departure': {
                                'airport': departure.get('iataCode', ''),
                                'time': departure.get('at', '')
                            },
                            'arrival': {
                                'airport': arrival.get('iataCode', ''),
                                'time': arrival.get('at', '')
                            },
                            'carrier': carrier_code,
                            'number': segment_number,
                            'flight_number': flight_number,  # Formatted flight number
                            'duration': segment.get('duration', '')
                        })
                        
                        # Extract outbound flight details from first itinerary
                        if itinerary_idx == 0:
                            if seg_idx == 0 and not outbound_flight_number and flight_number:
                                outbound_flight_number = flight_number
                        # Extract return flight details from second itinerary
                        elif itinerary_idx == 1:
                            if seg_idx == 0:
                                if not return_flight_number and flight_number:
                                    return_flight_number = flight_number
                                if not return_departure_time:
                                    return_departure_time = departure.get('at', '')
                                if not return_departure_airport:
                                    return_departure_airport = departure.get('iataCode', '')
                            # Last segment of return itinerary
                            if seg_idx == len(itinerary_segments) - 1:
                                if not return_arrival_time:
                                    return_arrival_time = arrival.get('at', '')
                                if not return_arrival_airport:
                                    return_arrival_airport = arrival.get('iataCode', '')
                
                # Extract unique airlines
                airlines = list(set([
                    segment.get('carrierCode', '')
                    for itinerary in itineraries
                    for segment in itinerary.get('segments', [])
                    if segment.get('carrierCode')
                ]))
                
                normalized_offer = {
                    'id': offer.get('id', ''),
                    'price': total_price,
                    'currency': currency,
                    'segments': segments,
                    'airlines': airlines,
                    'number_of_bookable_seats': offer.get('numberOfBookableSeats', 0),
                    'one_way': not return_date,
                    'flight_number': outbound_flight_number,  # Formatted outbound flight number (e.g., "KL1005")
                    'return_flight_number': return_flight_number,  # Formatted return flight number (if round trip)
                    'return_departure_time': return_departure_time,  # Return departure time (ISO format)
                    'return_arrival_time': return_arrival_time,  # Return arrival time (ISO format)
                    'return_departure_airport': return_departure_airport,  # Return departure airport code
                    'return_arrival_airport': return_arrival_airport  # Return arrival airport code
                }
                
                flight_options.append(normalized_offer)
                logger.debug(f"Normalized offer: {normalized_offer['id']} - {total_price} {currency}")
        
        logger.info(f"Found {len(flight_options)} flight options" +
                   (f" (filtered from {len(response.data)} total)" if max_price else ""))
        
        # Prepare result (before max_price filtering for caching)
        result = {
            'flight_options': flight_options,
            'search_params': {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'return_date': return_date,
                'adults': adults
            },
            'source': 'api'
        }
        
        # Cache the result (cache before max_price filtering so we can reuse it)
        search_cache.set(origin, destination, departure_date, return_date, adults, result)
        logger.debug(f"Cached flight search result")
        
        # Apply max_price filter if specified (after caching)
        if max_price:
            filtered_options = [
                opt for opt in result['flight_options']
                if opt.get('price', float('inf')) <= max_price
            ]
            result = result.copy()
            result['flight_options'] = filtered_options
            logger.debug(f"Applied max_price filter: {len(filtered_options)} options remaining")
        
        # Log full tool output
        logger.info("=" * 80)
        logger.info(f"=== TOOL OUTPUT: search_flights ===")
        logger.info("=" * 80)
        logger.info(f"Request ID: {request_id}")
        logger.info(f"Output Summary: {len(result.get('flight_options', []))} flight options found")
        logger.info(f"Full Tool Output: {json.dumps(result, indent=2, default=str)}")
        logger.info("=" * 80)
        
        return result
        
    except NetworkError as error:
        # NetworkError is a specific Amadeus error for network issues
        # This happens when the MCP sandbox blocks network access
        # Return empty results instead of crashing - the LLM can still function
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        logger.warning(f"Network error connecting to Amadeus API: {error_desc}")
        logger.warning(f"Returning empty results for {origin} -> {destination} - API unavailable")
        return {
            'flight_options': [],
            'source': 'network_error',
            'error': f'API unavailable for flight search',
            'search_params': {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'return_date': return_date,
                'adults': adults
            }
        }
        
    except ResponseError as error:
        error_type = type(error).__name__
        error_code = getattr(error, 'code', None)
        # description is a METHOD, not a property - call it!
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        
        # For rate limit errors, return empty results gracefully
        if error_code == 429:
            logger.warning(f"Rate limited by Amadeus API for flight search {origin} -> {destination}")
            return {
                'flight_options': [],
                'source': 'rate_limited',
                'error': 'API rate limit exceeded',
                'search_params': {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date,
                    'return_date': return_date,
                    'adults': adults
                }
            }
        
        logger.error(f"Amadeus API error: {error_type} (code={error_code}): {error_desc}")
        raise Exception(f"Failed to search flights: {error_type} (code={error_code}) - {error_desc}")
    except Exception as error:
        error_str = str(error)
        error_type = type(error).__name__
        
        logger.error(f"Unexpected error: {error_type}: {error_str}", exc_info=True)
        raise Exception(f"Failed to search flights: {error_type}: {error_str}")

