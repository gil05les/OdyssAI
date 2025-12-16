"""
Get car offer details tool.
Retrieves detailed information about a specific car rental offer.
"""
import time
from typing import Dict, Any, Optional
from amadeus.client.errors import ResponseError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger


def get_car_offer_details(
    offer_id: str,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific car rental offer.
    
    Args:
        offer_id: Car rental offer ID from search results
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with detailed offer information including:
        - Vehicle specifications
        - Insurance details
        - Pricing breakdown
        - Cancellation policy
        - Terms and conditions
    
    Example:
        Input: {"offer_id": "OFFER_123"}
        Output: {
            "offer_details": {...},
            "insurance": {...},
            "cancellation_policy": {...}
        }
    """
    request_id = f"offer_details_{int(time.time() * 1000)}"
    logger = get_logger("get_car_offer_details", request_id)
    
    try:
        logger.info(f"Getting details for car rental offer: {offer_id}")
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        logger.debug(f"Calling Amadeus API: GET /v1/shopping/car-rental-offers/{offer_id}")
        
        start_time = time.time()
        
        # Call Amadeus API using generic get method
        # Note: Car rental API might not be available in test environment
        response = None
        error = None
        
        # Try 1: Direct get method
        try:
            response = amadeus.get(f'/v1/shopping/car-rental-offers/{offer_id}')
        except Exception as e1:
            error = e1
            logger.debug(f"Method 1 failed: {e1}")
            
            # Try 2: Check if there's a car_rental_offer method in shopping
            try:
                if hasattr(amadeus.shopping, 'car_rental_offer'):
                    response = amadeus.shopping.car_rental_offer(offer_id).get()
            except Exception as e2:
                logger.debug(f"Method 2 failed: {e2}")
                
                # Try 3: Use shopping.get with full path
                try:
                    response = amadeus.shopping.get(f'/v1/shopping/car-rental-offers/{offer_id}')
                except Exception as e3:
                    logger.debug(f"Method 3 failed: {e3}")
                    raise error  # Raise original error
        
        if response is None:
            raise Exception("All API call methods failed")
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s")
        
        # Extract and normalize offer details
        if not response.data:
            raise Exception("No offer data returned from API")
        
        offer_data = response.data[0] if isinstance(response.data, list) else response.data
        
        # Extract vehicle information
        vehicle = offer_data.get('vehicle', {})
        
        # Extract pricing information
        pricing = offer_data.get('pricing', {})
        
        # Extract insurance information
        insurance = offer_data.get('insurance', [])
        
        # Extract cancellation policy
        cancellation_policy = offer_data.get('cancellationPolicy', {})
        
        # Extract terms and conditions
        terms = offer_data.get('terms', {})
        
        # Build normalized response
        normalized_details = {
            'offer_id': offer_data.get('id', ''),
            'provider': {
                'name': offer_data.get('provider', {}).get('name', ''),
                'code': offer_data.get('provider', {}).get('code', '')
            },
            'vehicle': {
                'category': vehicle.get('category', ''),
                'make': vehicle.get('make', ''),
                'model': vehicle.get('model', ''),
                'transmission': vehicle.get('transmission', ''),
                'air_conditioning': vehicle.get('airConditioning', False),
                'fuel': vehicle.get('fuel', ''),
                'seats': vehicle.get('seats', 0),
                'doors': vehicle.get('doors', 0),
                'luggage_capacity': vehicle.get('luggageCapacity', {}),
                'features': vehicle.get('features', [])
            },
            'pricing': {
                'total': float(pricing.get('total', 0)) if pricing.get('total') else 0,
                'currency': pricing.get('currency', 'CHF'),
                'base': float(pricing.get('base', 0)) if pricing.get('base') else 0,
                'taxes': [
                    {
                        'amount': float(tax.get('amount', 0)),
                        'code': tax.get('code', ''),
                        'description': tax.get('description', '')
                    }
                    for tax in pricing.get('taxes', [])
                ],
                'fees': [
                    {
                        'amount': float(fee.get('amount', 0)),
                        'code': fee.get('code', ''),
                        'description': fee.get('description', '')
                    }
                    for fee in pricing.get('fees', [])
                ]
            },
            'insurance': [
                {
                    'type': ins.get('type', ''),
                    'included': ins.get('included', False),
                    'coverage': ins.get('coverage', {}),
                    'description': ins.get('description', '')
                }
                for ins in insurance
            ],
            'cancellation_policy': {
                'type': cancellation_policy.get('type', ''),
                'deadline': cancellation_policy.get('deadline', ''),
                'penalty': cancellation_policy.get('penalty', {}),
                'description': cancellation_policy.get('description', '')
            },
            'terms': {
                'mileage': terms.get('mileage', {}),
                'age_requirements': terms.get('ageRequirements', {}),
                'driver_requirements': terms.get('driverRequirements', []),
                'additional_info': terms.get('additionalInfo', '')
            },
            'pickup_location': offer_data.get('pickupLocation', {}),
            'dropoff_location': offer_data.get('dropoffLocation', {}),
            'pickup_datetime': offer_data.get('pickupDateTime', ''),
            'dropoff_datetime': offer_data.get('dropoffDateTime', '')
        }
        
        logger.info(f"Retrieved details for offer: {normalized_details['vehicle']['make']} {normalized_details['vehicle']['model']}")
        logger.debug(f"Price: {normalized_details['pricing']['total']} {normalized_details['pricing']['currency']}")
        logger.debug(f"Insurance included: {len([i for i in normalized_details['insurance'] if i.get('included')])} items")
        
        return {
            'offer_details': normalized_details,
            'offer_id': offer_id
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
        raise Exception(f"Failed to get car offer details: {error_msg}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to get car offer details: {str(error)}")

