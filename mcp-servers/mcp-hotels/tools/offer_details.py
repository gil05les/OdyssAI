"""
Get hotel offer details tool.
Retrieves detailed information about a specific hotel offer.
"""
import time
from typing import Dict, Any, Optional
from amadeus.client.errors import ResponseError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger


def get_hotel_offer_details(
    offer_id: str,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific hotel offer.
    
    Args:
        offer_id: Hotel offer ID from search results
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with detailed offer information including:
        - Room details (size, type, description)
        - Cancellation policies
        - Price breakdown
        - Hotel information
        - Amenities
    
    Example:
        Input: {"offer_id": "OFFER_123"}
        Output: {
            "offer": {...},
            "room_details": {...},
            "cancellation_policy": {...},
            "price_breakdown": {...}
        }
    """
    request_id = f"offer_details_{int(time.time() * 1000)}"
    logger = get_logger("get_hotel_offer_details", request_id)
    
    try:
        logger.info(f"Getting details for hotel offer: {offer_id}")
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        logger.debug(f"Calling Amadeus API: GET /v3/shopping/hotel-offers/{offer_id}")
        
        start_time = time.time()
        
        # Call Amadeus API
        # hotel_offer_search is a method that returns an object with get()
        # The offer_id is passed to hotel_offer_search, then we call get()
        response = amadeus.shopping.hotel_offer_search(offer_id).get()
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s")
        
        # Extract and normalize offer details
        if not response.data:
            raise Exception("No offer data returned from API")
        
        offer_data = response.data[0] if isinstance(response.data, list) else response.data
        
        # Extract hotel information
        hotel_info = offer_data.get('hotel', {})
        
        # Extract offer details
        offers = offer_data.get('offers', [])
        if not offers:
            raise Exception("No offers found in response")
        
        # Get the first offer (or match by offer_id if multiple)
        offer = None
        for o in offers:
            if o.get('id') == offer_id:
                offer = o
                break
        if not offer:
            offer = offers[0]  # Use first offer if ID doesn't match
        
        # Extract room information
        room = offer.get('room', {})
        room_type = room.get('typeEstimated', {})
        room_description = room.get('description', {})
        
        # Extract cancellation policy
        cancellation_policy = offer.get('policies', {}).get('cancellation', {})
        
        # Extract price information
        price = offer.get('price', {})
        price_variations = offer.get('priceVariations', [])
        
        # Extract amenities
        amenities = hotel_info.get('amenities', [])
        
        # Build normalized response
        normalized_details = {
            'offer_id': offer.get('id', ''),
            'hotel': {
                'hotel_id': hotel_info.get('hotelId', ''),
                'name': hotel_info.get('name', ''),
                'rating': hotel_info.get('rating', ''),
                'contact': hotel_info.get('contact', {}),
                'address': hotel_info.get('address', {}),
                'amenities': amenities
            },
            'room': {
                'type': room_type.get('category', ''),
                'beds': room_type.get('beds', 0),
                'bed_type': room_type.get('bedType', ''),
                'description': room_description.get('text', ''),
                'room_type_code': room.get('type', '')
            },
            'price': {
                'total': float(price.get('total', 0)),
                'currency': price.get('currency', 'CHF'),
                'base': float(price.get('base', 0)),
                'taxes': [
                    {
                        'amount': float(tax.get('amount', 0)),
                        'code': tax.get('code', ''),
                        'percentage': tax.get('percentage', 0)
                    }
                    for tax in price.get('taxes', [])
                ],
                'variations': [
                    {
                        'start_date': var.get('startDate', ''),
                        'end_date': var.get('endDate', ''),
                        'total': float(var.get('total', 0))
                    }
                    for var in price_variations
                ]
            },
            'cancellation_policy': {
                'type': cancellation_policy.get('type', ''),
                'amount': float(cancellation_policy.get('amount', 0)) if cancellation_policy.get('amount') else None,
                'number_of_nights': cancellation_policy.get('numberOfNights', 0),
                'deadline': cancellation_policy.get('deadline', ''),
                'description': cancellation_policy.get('description', '')
            },
            'check_in': offer_data.get('checkInDate', ''),
            'check_out': offer_data.get('checkOutDate', ''),
            'guests': offer_data.get('guests', {}),
            'self': offer.get('self', ''),
            'booking_required': offer.get('bookingRequired', False)
        }
        
        logger.info(f"Retrieved details for offer: {normalized_details['hotel']['name']}")
        logger.debug(f"Price: {normalized_details['price']['total']} {normalized_details['price']['currency']}")
        
        return {
            'offer_details': normalized_details,
            'offer_id': offer_id
        }
        
    except ResponseError as error:
        # Try to get more detailed error information
        error_parts = [str(error)]
        try:
            if hasattr(error, 'response') and error.response:
                if hasattr(error.response, 'body'):
                    body = error.response.body
                    if isinstance(body, dict):
                        if 'errors' in body:
                            for err in body['errors']:
                                if 'detail' in err:
                                    error_parts.append(f"Detail: {err['detail']}")
                        elif 'detail' in body:
                            error_parts.append(f"Detail: {body['detail']}")
        except Exception:
            pass
        
        error_msg = " | ".join(error_parts)
        logger.error(f"Amadeus API error: {error_msg}")
        raise Exception(f"Failed to get hotel offer details: {error_msg}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to get hotel offer details: {str(error)}")

