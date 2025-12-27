"""
Extract itinerary preferences from trip history.
Analyzes activity categories, pace, and activity budget.
"""
import time
from typing import Dict, Any, List, Optional
from collections import Counter
from db_client import PreferencesDBClient
from logger import get_logger


def get_itinerary_preferences(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Extract itinerary preferences from user's trip history.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with itinerary preferences or no_preference indicators
    """
    request_id = f"itinerary_prefs_{int(time.time() * 1000)}"
    logger = get_logger("itinerary_preferences", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        trips = client.get_user_trips(user_id)
        
        # Collect all activities across all trips
        all_activities = []
        trip_durations = []
        
        for trip in trips:
            trip_data = trip.get("trip_data", {})
            trip_state = trip_data.get("tripState", {})
            trip_request = trip_data.get("tripRequest", {})
            
            activities = trip_state.get("activities", [])
            if isinstance(activities, list):
                all_activities.extend(activities)
            
            # Get trip duration from date ranges
            date_ranges = trip_request.get("date_ranges", [])
            if date_ranges and len(date_ranges) > 0:
                # Estimate duration from first date range
                date_range = date_ranges[0]
                if "from" in date_range and "to" in date_range:
                    try:
                        from datetime import datetime
                        from_date = datetime.strptime(date_range["from"], "%Y-%m-%d")
                        to_date = datetime.strptime(date_range["to"], "%Y-%m-%d")
                        duration = (to_date - from_date).days
                        if duration > 0:
                            trip_durations.append(duration)
                    except (ValueError, KeyError):
                        pass
        
        if len(all_activities) < 10:
            return {
                "user_id": user_id,
                "trip_count": len(trips),
                "activities_count": len(all_activities),
                "has_preference": False,
                "reason": f"Insufficient data: only {len(all_activities)} activity/activities selected across all trips. Need at least 10 activities to establish preferences.",
                "preferences": None
            }
        
        # Aggregate activity data
        categories = Counter()
        prices = []
        
        for activity in all_activities:
            # Category
            category = activity.get("category")
            if category:
                categories[category] += 1
            
            # Price
            price = activity.get("price")
            if price and price > 0:
                prices.append(price)
        
        # Calculate average activities per day
        avg_activities_per_day = None
        if trip_durations:
            total_days = sum(trip_durations)
            if total_days > 0:
                avg_activities_per_day = round(len(all_activities) / total_days, 1)
        
        # Determine pace preference
        if avg_activities_per_day:
            if avg_activities_per_day < 2:
                pace_preference = "relaxed"
            elif avg_activities_per_day < 4:
                pace_preference = "moderate"
            else:
                pace_preference = "active"
        else:
            pace_preference = "no_preference"
        
        # Calculate activity budget
        avg_price = round(sum(prices) / len(prices), 2) if prices else None
        total_per_trip = round(sum(prices) / len(trips), 2) if prices and trips else None
        
        preferences = {
            "favorite_categories": dict(categories.most_common(10)),
            "avg_activities_per_day": avg_activities_per_day,
            "activity_budget": {
                "avg_price": avg_price,
                "total_per_trip": total_per_trip
            },
            "pace_preference": pace_preference
        }
        
        return {
            "user_id": user_id,
            "trip_count": len(trips),
            "activities_count": len(all_activities),
            "has_preference": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error extracting itinerary preferences: {e}", exc_info=True)
        raise Exception(f"Failed to extract itinerary preferences: {str(e)}")

