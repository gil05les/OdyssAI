"""
Search activities tool.
Finds businesses/activities using the Yelp Fusion API.
"""
import time
import socket
from typing import Dict, Any, List, Optional

from yelp_client import YelpClient
from logger import get_logger


def search_activities(
    location: str,
    category: str = "restaurants",
    limit: int = 10,
    sort_by: str = "rating",
    client: Optional[YelpClient] = None
) -> Dict[str, Any]:
    """
    Search for activities/businesses in a location using Yelp.
    
    Args:
        location: City/location to search (e.g., "St. Gallen, Switzerland")
        category: Business category - restaurants, bars, museums, attractions, etc.
        limit: Number of results to return (max 50)
        sort_by: Sort order - best_match, rating, review_count, distance
        client: Yelp client instance (optional)
    
    Returns:
        Dictionary with activities list and metadata including Yelp URLs
    
    Example:
        Input: {
            "location": "St. Gallen, Switzerland",
            "category": "museums",
            "limit": 5
        }
        Output: {
            "activities": [...],
            "total_found": 10,
            "category": "museums",
            "location": "St. Gallen, Switzerland"
        }
    """
    request_id = f"activities_{int(time.time() * 1000)}"
    logger = get_logger("search_activities", request_id)
    
    try:
        logger.info(f"Searching activities: {location} - {category} (limit: {limit})")
        
        # Initialize client if not provided
        if client is None:
            client = YelpClient()
        
        # Add initial delay for sandbox network setup
        initial_delay = 1.0
        logger.debug(f"Waiting {initial_delay}s for network setup...")
        time.sleep(initial_delay)
        
        # Call Yelp API with retry logic
        max_retries = 3
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                logger.info(f"Calling Yelp API (attempt {retry_count + 1}/{max_retries + 1})...")
                response = client.search_businesses(
                    location=location,
                    category=category,
                    limit=limit,
                    sort_by=sort_by
                )
                logger.info("Yelp API call successful")
                break
            except (socket.timeout, TimeoutError) as error:
                retry_count += 1
                logger.warning(f"Timeout error (attempt {retry_count}/{max_retries + 1}): {error}")
                
                if retry_count <= max_retries:
                    delay = 2.0 * retry_count
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise Exception(f"Failed after {max_retries + 1} attempts: timeout")
            except Exception as error:
                retry_count += 1
                logger.warning(f"Error (attempt {retry_count}/{max_retries + 1}): {error}")
                
                if retry_count <= max_retries:
                    delay = 2.0 * retry_count
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise
        
        if not response:
            return {
                'activities': [],
                'total_found': 0,
                'category': category,
                'location': location,
                'message': 'No response from Yelp API'
            }
        
        # Normalize businesses to activities format
        activities = []
        businesses = response.get("businesses", [])
        
        for business in businesses:
            # Extract location info
            location_info = business.get("location", {})
            address_parts = location_info.get("display_address", [])
            address = ", ".join(address_parts) if address_parts else "Address not available"
            
            # Extract categories
            categories = business.get("categories", [])
            category_names = [cat.get("title", "") for cat in categories]
            
            # Extract coordinates
            coordinates = business.get("coordinates", {})
            
            activity = {
                'id': business.get("id", ""),
                'name': business.get("name", "Unknown"),
                'rating': business.get("rating"),
                'review_count': business.get("review_count", 0),
                'price': business.get("price", "N/A"),
                'address': address,
                'city': location_info.get("city", ""),
                'country': location_info.get("country", ""),
                'phone': business.get("display_phone", ""),
                'categories': category_names,
                'image_url': business.get("image_url", ""),
                'yelp_url': business.get("url", ""),  # Clickable Yelp link
                'distance_meters': business.get("distance"),
                'is_closed': business.get("is_closed", False),
                'latitude': coordinates.get("latitude"),
                'longitude': coordinates.get("longitude"),
                # Source indicator for frontend
                'source': 'yelp'
            }
            
            activities.append(activity)
            logger.debug(f"Added: {activity['name']} - {activity['rating']}⭐")
        
        logger.info(f"Found {len(activities)} activities")
        
        return {
            'activities': activities,
            'total_found': response.get("total", len(activities)),
            'category': category,
            'location': location,
            'source': 'yelp'
        }
        
    except ValueError as error:
        logger.error(f"API key error: {error}")
        return {
            'activities': [],
            'total_found': 0,
            'category': category,
            'location': location,
            'error': str(error),
            'source': 'yelp'
        }
    except Exception as error:
        logger.error(f"Unexpected error: {error}", exc_info=True)
        raise Exception(f"Failed to search activities: {str(error)}")


def get_yelp_categories() -> Dict[str, str]:
    """
    Get available Yelp category mappings.
    
    Returns:
        Dictionary mapping category keys to display names
    """
    return YelpClient.get_available_categories()

