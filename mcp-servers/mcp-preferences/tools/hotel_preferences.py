"""
Extract hotel preferences from trip history.
Analyzes star ratings, amenities, price range, and location types.
"""
import time
from typing import Dict, Any, List, Optional
from collections import Counter
from db_client import PreferencesDBClient
from logger import get_logger


def get_hotel_preferences(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Extract hotel preferences from user's trip history.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with hotel preferences or no_preference indicators
    """
    request_id = f"hotel_prefs_{int(time.time() * 1000)}"
    logger = get_logger("hotel_preferences", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        trips = client.get_user_trips(user_id)
        
        # Filter trips with hotels
        hotels = []
        for trip in trips:
            trip_data = trip.get("trip_data", {})
            trip_state = trip_data.get("tripState", {})
            hotel = trip_state.get("hotel")
            if hotel:
                hotels.append(hotel)
        
        if len(hotels) < 3:
            return {
                "user_id": user_id,
                "trip_count": len(trips),
                "hotels_count": len(hotels),
                "has_preference": False,
                "reason": f"Insufficient data: only {len(hotels)} hotel(s) booked. Need at least 3 hotels to establish preferences.",
                "preferences": None
            }
        
        # Aggregate hotel data
        star_ratings = []
        prices = []
        all_amenities = Counter()
        locations = []
        
        for hotel in hotels:
            # Star rating
            stars = hotel.get("stars")
            if stars:
                star_ratings.append(stars)
            
            # Price per night
            price = hotel.get("pricePerNight")
            if price:
                prices.append(price)
            
            # Amenities
            amenities = hotel.get("amenities", [])
            for amenity in amenities:
                all_amenities[amenity] += 1
            
            # Location
            location = hotel.get("location", "")
            if location:
                locations.append(location.lower())
        
        # Check star rating variance
        if star_ratings:
            min_stars = min(star_ratings)
            max_stars = max(star_ratings)
            if max_stars - min_stars >= 3:
                return {
                    "user_id": user_id,
                    "trip_count": len(trips),
                    "hotels_count": len(hotels),
                    "has_preference": False,
                    "reason": f"Star ratings span too wide a range ({min_stars}-{max_stars} stars). No clear preference.",
                    "preferences": None
                }
        
        # Calculate preferences
        avg_stars = round(sum(star_ratings) / len(star_ratings), 1) if star_ratings else None
        most_common_stars = Counter(star_ratings).most_common(1)[0][0] if star_ratings else None
        
        avg_price = round(sum(prices) / len(prices), 2) if prices else None
        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
        
        # Infer location type
        location_type = _infer_location_type(locations)
        
        preferences = {
            "preferred_star_rating": {
                "average": avg_stars,
                "most_common": most_common_stars
            },
            "price_range": {
                "avg_per_night": avg_price,
                "min_selected": min_price,
                "max_selected": max_price
            },
            "preferred_amenities": dict(all_amenities.most_common(15)),
            "location_type": location_type
        }
        
        return {
            "user_id": user_id,
            "trip_count": len(trips),
            "hotels_count": len(hotels),
            "has_preference": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error extracting hotel preferences: {e}", exc_info=True)
        raise Exception(f"Failed to extract hotel preferences: {str(e)}")


def _infer_location_type(locations: List[str]) -> str:
    """
    Infer location type from hotel location strings.
    """
    if not locations:
        return "no_preference"
    
    location_text = " ".join(locations).lower()
    
    # Check for keywords
    if any(word in location_text for word in ["beach", "beachfront", "coast", "seaside", "waterfront"]):
        return "beachfront"
    elif any(word in location_text for word in ["center", "downtown", "city", "town"]):
        return "city_center"
    elif any(word in location_text for word in ["view", "scenic", "cliff", "mountain", "hill"]):
        return "scenic"
    else:
        return "no_preference"

