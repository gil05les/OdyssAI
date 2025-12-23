"""
Search hotels in city tool.
Finds hotels in a specific city with price and guest filters.
"""
import time
from typing import Dict, Any, Optional
from amadeus.client.errors import ResponseError, NetworkError

from amadeus_client import AmadeusClientWrapper
from logger import get_logger


def search_hotels_in_city(
    city_code: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    max_price_per_night: Optional[float] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    """
    Search for hotels in a specific city.
    
    Args:
        city_code: IATA city code (e.g., "LIS" for Lisbon)
        check_in: Check-in date in YYYY-MM-DD format (e.g., "2025-05-10")
        check_out: Check-out date in YYYY-MM-DD format (e.g., "2025-05-17")
        guests: Number of guests (default: 1)
        max_price_per_night: Optional maximum price per night filter
        client: Amadeus client wrapper instance
    
    Returns:
        Dictionary with hotel offers
    
    Example:
        Input: {
            "city_code": "LIS",
            "check_in": "2025-05-10",
            "check_out": "2025-05-17",
            "guests": 2,
            "max_price_per_night": 150
        }
        Output: {
            "hotel_offers": [...],
            "total_offers": 10
        }
    """
    request_id = f"search_city_{int(time.time() * 1000)}"
    logger = get_logger("search_hotels_in_city", request_id)
    
    try:
        logger.info(
            f"Searching hotels in city: {city_code} "
            f"from {check_in} to {check_out} "
            f"for {guests} guest(s)"
        )
        
        # Initialize client if not provided
        if client is None:
            client = AmadeusClientWrapper()
        
        amadeus = client.get_client()
        
        # Step 1: Get hotel IDs in the city
        logger.debug("Step 1: Getting hotel IDs by city")
        logger.debug(f"Calling: GET /v1/reference-data/locations/hotels/by-city")
        
        start_time = time.time()
        
        # Add initial delay to allow sandbox network rules to be set up
        initial_delay = 2.0  # 2 seconds for network setup
        logger.debug(f"Waiting {initial_delay}s for sandbox network setup...")
        time.sleep(initial_delay)
        
        # Call Amadeus API with retry logic for NetworkError and socket.timeout
        # NetworkError can occur when sandbox network rules aren't ready yet
        # socket.timeout can occur if the API is slow to respond
        import socket
        max_retries = 5
        retry_count = 0
        hotels_response = None
        
        while retry_count <= max_retries:
            try:
                # Get hotels in the city
                logger.info(f"Calling hotels by city API (attempt {retry_count + 1}/{max_retries + 1})...")
                hotels_response = amadeus.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code
                )
                logger.info(f"Hotels by city API call successful")
                break  # Success, exit retry loop
            except (NetworkError, socket.timeout) as error:
                retry_count += 1
                if isinstance(error, socket.timeout):
                    error_desc = f"Socket timeout after 30 seconds"
                else:
                    error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
                logger.warning(f"Network/timeout error (attempt {retry_count}/{max_retries + 1}): {error_desc}")
                
                if retry_count <= max_retries:
                    # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                    delay = 2.0 * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {delay:.1f}s (sandbox network may still be initializing)...")
                    time.sleep(delay)
                else:
                    # Max retries reached, re-raise to be caught by outer handler
                    raise Exception(f"Failed to get hotels after {max_retries + 1} attempts: {error_desc}")
        
        try:
            
            hotel_ids = []
            if hotels_response.data:
                for hotel in hotels_response.data:
                    hotel_id = hotel.get('hotelId', '')
                    if hotel_id:
                        hotel_ids.append(hotel_id)
            
            logger.info(f"Found {len(hotel_ids)} hotels in {city_code}")
            
            if not hotel_ids:
                return {
                    'hotel_offers': [],
                    'total_offers': 0,
                    'city_code': city_code,
                    'message': f'No hotels found in {city_code}'
                }
            
            # Step 2: Get hotel offers
            logger.debug("Step 2: Getting hotel offers")
            logger.debug(f"Calling: GET /v3/shopping/hotel-offers")
            
            # Build parameters for hotel offers search
            params = {
                'hotelIds': ','.join(hotel_ids[:50]),  # Limit to first 50 hotels
                'checkInDate': check_in,
                'checkOutDate': check_out,
                'adults': guests
            }
            
            logger.debug(f"Parameters: {params}")
            
            # Call hotel offers API with retry logic for NetworkError and socket.timeout
            retry_count_offers = 0
            offers_response = None
            
            while retry_count_offers <= max_retries:
                try:
                    # Use hotel_offers_search (not hotel_offers)
                    logger.info(f"Calling hotel offers API (attempt {retry_count_offers + 1}/{max_retries + 1})...")
                    offers_response = amadeus.shopping.hotel_offers_search.get(**params)
                    logger.info(f"Hotel offers API call successful")
                    break  # Success, exit retry loop
                except (NetworkError, socket.timeout) as error:
                    retry_count_offers += 1
                    if isinstance(error, socket.timeout):
                        error_desc = f"Socket timeout after 30 seconds"
                    else:
                        error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
                    logger.warning(f"Network/timeout error on hotel offers (attempt {retry_count_offers}/{max_retries + 1}): {error_desc}")
                    
                    if retry_count_offers <= max_retries:
                        # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                        delay = 2.0 * (2 ** (retry_count_offers - 1))
                        logger.info(f"Retrying hotel offers in {delay:.1f}s (sandbox network may still be initializing)...")
                        time.sleep(delay)
                    else:
                        # Max retries reached, re-raise to be caught by outer handler
                        raise Exception(f"Failed to get hotel offers after {max_retries + 1} attempts: {error_desc}")
            
            duration = time.time() - start_time
            logger.info(f"API calls completed in {duration:.3f}s (after {retry_count + retry_count_offers} retries)")
            
            # Check if we got a valid response
            if not offers_response:
                logger.warning("No response from hotel offers API")
                return {
                    'hotel_offers': [],
                    'total_offers': 0,
                    'city_code': city_code,
                    'message': 'No response from hotel offers API'
                }
            
            # Normalize and filter offers
            hotel_offers = []
            if offers_response.data:
                for hotel_data in offers_response.data:
                    hotel_info = hotel_data.get('hotel', {})
                    hotel_id = hotel_info.get('hotelId', '')
                    hotel_name = hotel_info.get('name', '')
                    # Extract rating if available (Amadeus may provide this)
                    hotel_rating = hotel_info.get('rating', None)
                    if hotel_rating:
                        try:
                            # Rating might be a string like "4.5" or a number
                            hotel_rating = float(hotel_rating) if hotel_rating else None
                        except (ValueError, TypeError):
                            hotel_rating = None
                    
                    offers = hotel_data.get('offers', [])
                    
                    for offer in offers:
                        # Extract price
                        price_info = offer.get('price', {})
                        total_price = float(price_info.get('total', 0))
                        currency = price_info.get('currency', 'CHF')
                        
                        # Calculate price per night
                        from datetime import datetime
                        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
                        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
                        nights = (check_out_date - check_in_date).days
                        price_per_night = total_price / nights if nights > 0 else total_price
                        
                        # Apply max_price_per_night filter
                        if max_price_per_night and price_per_night > max_price_per_night:
                            logger.debug(
                                f"Skipping offer - price per night {price_per_night:.2f} "
                                f"exceeds max {max_price_per_night}"
                            )
                            continue
                        
                        # Generate image URL using different stock hotel images
                        # Using a variety of hotel stock photos from Unsplash
                        # Each hotel gets a different image based on its index
                        hotel_stock_images = [
                            'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80',  # Modern luxury hotel
                            'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80',  # Elegant hotel lobby
                            'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&q=80',  # Hotel room with view
                            'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800&q=80',  # Resort pool area
                            'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&q=80',  # Hotel exterior
                            'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&q=80',  # Luxury suite
                            'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800&q=80',  # Modern hotel room
                            'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&q=80',  # Hotel balcony view
                            'https://images.unsplash.com/photo-1596436889106-be35e843f974?w=800&q=80',  # Boutique hotel
                            'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800&q=80',  # Hotel restaurant
                            'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&q=80',  # Spa area
                            'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800&q=80',  # Hotel pool
                        ]
                        # Use hotel ID hash to select a consistent image for each hotel
                        import hashlib
                        hotel_hash = int(hashlib.md5(hotel_id.encode()).hexdigest(), 16)
                        image_index = hotel_hash % len(hotel_stock_images)
                        image_url = hotel_stock_images[image_index]
                        
                        normalized_offer = {
                            'offer_id': offer.get('id', ''),
                            'hotel_id': hotel_id,
                            'hotel_name': hotel_name,
                            'hotel_rating': hotel_rating,
                            'image_url': image_url,
                            'price_total': total_price,
                            'price_per_night': round(price_per_night, 2),
                            'currency': currency,
                            'room_type': offer.get('room', {}).get('typeEstimated', {}).get('category', ''),
                            'room_description': offer.get('room', {}).get('description', {}).get('text', ''),
                            'check_in': check_in,
                            'check_out': check_out,
                            'guests': guests,
                            'nights': nights
                        }
                        
                        hotel_offers.append(normalized_offer)
                        logger.debug(
                            f"Normalized offer: {hotel_name} - "
                            f"{price_per_night:.2f} {currency}/night"
                        )
            
            logger.info(
                f"Found {len(hotel_offers)} hotel offers" +
                (f" (filtered from {sum(len(h.get('offers', [])) for h in offers_response.data)} total)" 
                 if max_price_per_night and offers_response and offers_response.data else "")
            )
            
            return {
                'hotel_offers': hotel_offers,
                'total_offers': len(hotel_offers),
                'city_code': city_code,
                'check_in': check_in,
                'check_out': check_out,
                'guests': guests
            }
            
        except NetworkError as error:
            error_desc = error.description() if callable(getattr(error, 'description', None)) else str(error)
            logger.error(f"Network error after retries: {error_desc}")
            raise Exception(f"Failed to search hotels: Network error - {error_desc}")
        except ResponseError as error:
            # Try to get more detailed error information
            error_parts = []
            try:
                # Get basic error info
                error_str = str(error) if error else "Unknown error"
                error_parts.append(f"Error: {error_str}")
                
                # Get error code if available
                if hasattr(error, 'code'):
                    error_parts.append(f"Code: {error.code}")
                
                # Get response body if available
                if hasattr(error, 'response') and error.response:
                    if hasattr(error.response, 'body'):
                        body = error.response.body
                        if isinstance(body, dict):
                            if 'errors' in body:
                                for err in body['errors']:
                                    if 'detail' in err:
                                        error_parts.append(f"Detail: {err['detail']}")
                                    if 'title' in err:
                                        error_parts.append(f"Title: {err['title']}")
                                    if 'code' in err:
                                        error_parts.append(f"Error Code: {err['code']}")
                            elif 'detail' in body:
                                error_parts.append(f"Detail: {body['detail']}")
                        elif isinstance(body, str):
                            error_parts.append(f"Response: {body}")
                    
                    # Get status code if available
                    if hasattr(error.response, 'status_code'):
                        error_parts.append(f"Status: {error.response.status_code}")
                
                # Log the full error object for debugging
                logger.debug(f"Full error object: {repr(error)}")
                logger.debug(f"Error type: {type(error)}")
                logger.debug(f"Error attributes: {dir(error)}")
            except Exception as e:
                logger.debug(f"Error extracting error details: {e}")
                error_parts.append(f"Could not extract details: {str(e)}")
            
            error_msg = " | ".join(error_parts) if error_parts else f"Unknown error: {type(error).__name__}"
            logger.error(f"Amadeus API error: {error_msg}")
            raise Exception(f"Failed to search hotels: {error_msg}")
        
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to search hotels: {str(error)}")

