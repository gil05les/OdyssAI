"""
Search cars at airport tool.
Finds rental cars available at a specific airport.
"""
import time
from typing import Dict, Any, Optional
from amadeus.client.errors import ResponseError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger


def search_cars_at_airport(
    pickup_iata: str,
    pickup_date: str,
    dropoff_date: str,
    pickup_time: Optional[str] = None,
    dropoff_time: Optional[str] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Search for rental cars at a specific airport.
    
    Args:
        pickup_iata: IATA code of the pickup airport (e.g., "LIS")
        pickup_date: Pickup date in YYYY-MM-DD format (e.g., "2025-05-10")
        dropoff_date: Dropoff date in YYYY-MM-DD format (e.g., "2025-05-17")
        pickup_time: Optional pickup time in HH:MM format (default: "10:00")
        dropoff_time: Optional dropoff time in HH:MM format (default: "10:00")
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with car rental offers
    
    Example:
        Input: {
            "pickup_iata": "LIS",
            "pickup_date": "2025-05-10",
            "dropoff_date": "2025-05-17"
        }
        Output: {
            "car_offers": [...],
            "total_offers": 10
        }
    """
    request_id = f"search_cars_{int(time.time() * 1000)}"
    logger = get_logger("search_cars_at_airport", request_id)
    
    try:
        # Default times if not provided
        if pickup_time is None:
            pickup_time = "10:00"
        if dropoff_time is None:
            dropoff_time = "10:00"
        
        logger.info(
            f"Searching cars at airport: {pickup_iata} "
            f"from {pickup_date} {pickup_time} "
            f"to {dropoff_date} {dropoff_time}"
        )
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Build parameters for car rental search
        # Format: pickupDateTime and dropoffDateTime should be in ISO 8601 format
        pickup_datetime = f"{pickup_date}T{pickup_time}:00"
        dropoff_datetime = f"{dropoff_date}T{dropoff_time}:00"
        
        params = {
            'pickupLocationCode': pickup_iata,
            'pickupDateTime': pickup_datetime,
            'dropoffLocationCode': pickup_iata,  # Same location for return
            'dropoffDateTime': dropoff_datetime
        }
        
        logger.debug(f"Calling Amadeus API: GET /v1/shopping/car-rental-offers")
        logger.debug(f"Parameters: {params}")
        
        start_time = time.time()
        
        # Call Amadeus API using generic get method
        # Note: Car rental API might not be available in test environment
        # Try multiple approaches
        response = None
        error = None
        
        # Try 1: Direct get method
        try:
            response = amadeus.get('/v1/shopping/car-rental-offers', params=params)
        except Exception as e1:
            error = e1
            logger.debug(f"Method 1 failed: {e1}")
            
            # Try 2: Check if there's a car_rental_offers method in shopping
            try:
                if hasattr(amadeus.shopping, 'car_rental_offers'):
                    response = amadeus.shopping.car_rental_offers.get(**params)
            except Exception as e2:
                logger.debug(f"Method 2 failed: {e2}")
                
                # Try 3: Use shopping.get with full path
                try:
                    response = amadeus.shopping.get('/v1/shopping/car-rental-offers', params=params)
                except Exception as e3:
                    logger.debug(f"Method 3 failed: {e3}")
                    raise error  # Raise original error
        
        if response is None:
            raise Exception("All API call methods failed")
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s")
        
        # Normalize response
        car_offers = []
        if response.data:
            for offer in response.data:
                # Extract car information
                vehicle = offer.get('vehicle', {})
                pricing = offer.get('pricing', {})
                
                normalized_offer = {
                    'offer_id': offer.get('id', ''),
                    'provider': offer.get('provider', {}).get('name', ''),
                    'vehicle': {
                        'category': vehicle.get('category', ''),
                        'make': vehicle.get('make', ''),
                        'model': vehicle.get('model', ''),
                        'transmission': vehicle.get('transmission', ''),
                        'air_conditioning': vehicle.get('airConditioning', False),
                        'fuel': vehicle.get('fuel', ''),
                        'seats': vehicle.get('seats', 0),
                        'doors': vehicle.get('doors', 0)
                    },
                    'pricing': {
                        'total': float(pricing.get('total', 0)) if pricing.get('total') else 0,
                        'currency': pricing.get('currency', 'CHF'),
                        'base': float(pricing.get('base', 0)) if pricing.get('base') else 0,
                        'taxes': [
                            {
                                'amount': float(tax.get('amount', 0)),
                                'code': tax.get('code', '')
                            }
                            for tax in pricing.get('taxes', [])
                        ]
                    },
                    'pickup_location': {
                        'code': pickup_iata,
                        'name': offer.get('pickupLocation', {}).get('name', '')
                    },
                    'dropoff_location': {
                        'code': pickup_iata,
                        'name': offer.get('dropoffLocation', {}).get('name', '')
                    },
                    'pickup_datetime': pickup_datetime,
                    'dropoff_datetime': dropoff_datetime,
                    'cancellation_policy': offer.get('cancellationPolicy', {}),
                    'insurance': offer.get('insurance', [])
                }
                car_offers.append(normalized_offer)
                logger.debug(
                    f"Normalized offer: {normalized_offer['vehicle']['make']} "
                    f"{normalized_offer['vehicle']['model']} - "
                    f"{normalized_offer['pricing']['total']} {normalized_offer['pricing']['currency']}"
                )
        
        logger.info(f"Found {len(car_offers)} car rental offers")
        
        return {
            'car_offers': car_offers,
            'total_offers': len(car_offers),
            'pickup_iata': pickup_iata,
            'pickup_date': pickup_date,
            'dropoff_date': dropoff_date
        }
        
    except ResponseError as error:
        # Try to get more detailed error information
        error_parts = [str(error)]
        error_code = getattr(error, 'code', None)
        
        # Check if it's a 404 (endpoint not found)
        if error_code == 404:
            error_parts.append(
                "Car rental API endpoint may not be available in test environment. "
                "This endpoint might require production credentials or may not be available in your Amadeus plan."
            )
        
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
        raise Exception(f"Failed to search cars: {error_msg}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to search cars: {str(error)}")

