"""
Price flight offer tool.
Gets final pricing for a flight offer before booking.
"""
import time
import json
from typing import Dict, Any, Optional
from amadeus.client.errors import ResponseError, NetworkError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger


def price_flight_offer(
    offer_id: str,
    offer_data: Optional[Dict[str, Any]] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Get final pricing for a flight offer.
    
    Note: The Amadeus API requires the full offer object, not just the ID.
    The offer_data should be the original offer from search_flights.
    
    Args:
        offer_id: Offer identifier (for logging/reference)
        offer_data: Full offer object from search_flights (required for API)
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with priced offer details including final price
    
    Example:
        Input: {"offer_id": "OFFER_123", "offer_data": {...}}
        Output: {
            "priced_offer": {...},
            "final_price": 420,
            "currency": "CHF"
        }
    """
    request_id = f"price_{int(time.time() * 1000)}"
    logger = get_logger("price_flight_offer", request_id)
    
    try:
        logger.info(f"Pricing flight offer: {offer_id}")
        
        if not offer_data:
            raise ValueError("offer_data is required for pricing. Provide the full offer object from search_flights.")
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Prepare request body - need to send the full offer data
        # The Amadeus API expects the offer in a specific format
        request_body = {
            'data': {
                'type': 'flight-offers-pricing',
                'flightOffers': [offer_data]
            }
        }
        
        logger.debug(f"Calling Amadeus API: POST /v2/shopping/flight-offers/pricing")
        logger.debug(f"Request body size: {len(json.dumps(request_body))} chars")
        
        # Add initial delay to allow sandbox network rules to be set up
        initial_delay = 2.0
        logger.debug(f"Waiting {initial_delay}s for sandbox network setup...")
        time.sleep(initial_delay)
        
        start_time = time.time()
        
        # Call Amadeus API with retry logic for NetworkError
        max_retries = 5
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                response = amadeus.shopping.flight_offers.pricing.post(request_body)
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
        
        # Extract priced offer
        if not response.data:
            raise Exception("No pricing data returned from API")
        
        priced_offer = response.data[0] if isinstance(response.data, list) else response.data
        
        # Extract final price
        price_info = priced_offer.get('price', {})
        final_price = float(price_info.get('total', 0))
        currency = price_info.get('currency', 'CHF')
        
        logger.info(f"Final price: {final_price} {currency}")
        logger.debug(f"Priced offer ID: {priced_offer.get('id', 'N/A')}")
        
        return {
            'priced_offer': priced_offer,
            'final_price': final_price,
            'currency': currency,
            'offer_id': offer_id,
            'pricing_guaranteed': priced_offer.get('pricingOptions', {}).get('priceType', '') == 'GUARANTEED'
        }
        
    except ValueError as error:
        logger.error(f"Validation error: {str(error)}")
        raise
    except NetworkError as error:
        # NetworkError is a specific Amadeus error for network issues
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        logger.warning(f"Network error connecting to Amadeus API: {error_desc}")
        logger.warning(f"Returning error for pricing offer {offer_id} - API unavailable")
        raise Exception(f"Failed to price flight offer: Network error - API unavailable")
    except ResponseError as error:
        error_type = type(error).__name__
        error_code = getattr(error, 'code', None)
        # description is a METHOD, not a property - call it!
        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
        
        # For rate limit errors, provide clear error message
        if error_code == 429:
            logger.warning(f"Rate limited by Amadeus API for pricing offer {offer_id}")
            raise Exception(f"Failed to price flight offer: API rate limit exceeded")
        
        logger.error(f"Amadeus API error: {error_type} (code={error_code}): {error_desc}")
        raise Exception(f"Failed to price flight offer: {error_type} (code={error_code}) - {error_desc}")
    except Exception as error:
        error_str = str(error)
        error_type = type(error).__name__
        
        logger.error(f"Unexpected error: {error_type}: {error_str}", exc_info=True)
        raise Exception(f"Failed to price flight offer: {error_type}: {error_str}")

