"""
Extract destination preferences from trip history.
Analyzes countries, regions, destination types, and surprise_me patterns.
"""
import time
from typing import Dict, Any, List, Optional
from collections import Counter
from db_client import PreferencesDBClient
from logger import get_logger

# Region mapping for countries
REGION_MAP = {
    # Europe
    "Greece": "Europe", "Italy": "Europe", "Spain": "Europe", "France": "Europe",
    "Portugal": "Europe", "Switzerland": "Europe", "Germany": "Europe", "Austria": "Europe",
    "Netherlands": "Europe", "Belgium": "Europe", "UK": "Europe", "Ireland": "Europe",
    "Norway": "Europe", "Sweden": "Europe", "Denmark": "Europe", "Finland": "Europe",
    "Iceland": "Europe", "Poland": "Europe", "Czech Republic": "Europe", "Croatia": "Europe",
    # Asia
    "Japan": "Asia", "Thailand": "Asia", "Indonesia": "Asia", "Singapore": "Asia",
    "Malaysia": "Asia", "Vietnam": "Asia", "South Korea": "Asia", "China": "Asia",
    "India": "Asia", "Philippines": "Asia", "Sri Lanka": "Asia", "Maldives": "Asia",
    # Americas
    "USA": "Americas", "United States": "Americas", "Canada": "Americas", "Mexico": "Americas",
    "Brazil": "Americas", "Argentina": "Americas", "Chile": "Americas", "Peru": "Americas",
    "Costa Rica": "Americas", "Colombia": "Americas",
    # Middle East & Africa
    "UAE": "Middle East", "United Arab Emirates": "Middle East", "Turkey": "Middle East",
    "Morocco": "Africa", "Egypt": "Africa", "South Africa": "Africa", "Kenya": "Africa",
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania"
}


def get_destination_preferences(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Extract destination preferences from user's trip history.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with destination preferences or no_preference indicators
    """
    request_id = f"dest_prefs_{int(time.time() * 1000)}"
    logger = get_logger("destination_preferences", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        trips = client.get_user_trips(user_id)
        
        # Filter trips with destinations
        trips_with_destinations = []
        surprise_me_count = 0
        
        for trip in trips:
            trip_data = trip.get("trip_data", {})
            trip_request = trip_data.get("tripRequest", {})
            trip_state = trip_data.get("tripState", {})
            
            destination = trip_state.get("destination")
            if destination:
                trips_with_destinations.append(trip)
            
            # Count surprise_me
            if trip_request.get("surprise_me"):
                surprise_me_count += 1
        
        total_trips = len(trips)
        
        if len(trips_with_destinations) < 3:
            return {
                "user_id": user_id,
                "trip_count": total_trips,
                "trips_with_destinations": len(trips_with_destinations),
                "has_preference": False,
                "reason": f"Insufficient data: only {len(trips_with_destinations)} trip(s) with destinations. Need at least 3 trips to establish destination preferences.",
                "preferences": None
            }
        
        # Aggregate destination data
        countries = Counter()
        regions = Counter()
        destination_names = Counter()
        
        for trip in trips_with_destinations:
            trip_data = trip.get("trip_data", {})
            trip_state = trip_data.get("tripState", {})
            destination = trip_state.get("destination", {})
            
            country = destination.get("country")
            name = destination.get("name")
            
            if country:
                countries[country] += 1
                # Map to region
                region = REGION_MAP.get(country, "Other")
                regions[region] += 1
            
            if name:
                destination_names[name] += 1
        
        # Check if all destinations are unique (no clear preference)
        if len(countries) == len(trips_with_destinations) and len(trips_with_destinations) <= 5:
            return {
                "user_id": user_id,
                "trip_count": len(trips),
                "trips_with_destinations": len(trips_with_destinations),
                "has_preference": False,
                "reason": "All destinations are unique - no clear preference pattern detected.",
                "preferences": None
            }
        
            # Calculate surprise_me ratio
        surprise_me_ratio = surprise_me_count / total_trips if total_trips > 0 else 0
        
        preferences = {
            "favorite_countries": dict(countries.most_common(10)),
            "favorite_regions": dict(regions.most_common(5)),
            "surprise_me_ratio": round(surprise_me_ratio, 2),
            "destination_types": _infer_destination_types(trips_with_destinations)
        }
        
        return {
            "user_id": user_id,
            "trip_count": total_trips,
            "trips_with_destinations": len(trips_with_destinations),
            "has_preference": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error extracting destination preferences: {e}", exc_info=True)
        raise Exception(f"Failed to extract destination preferences: {str(e)}")


def _infer_destination_types(trips: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Infer destination types from trip data.
    Looks at environments and destination characteristics.
    """
    types = Counter()
    
    for trip in trips:
        trip_data = trip.get("trip_data", {})
        trip_request = trip_data.get("tripRequest", {})
        trip_state = trip_data.get("tripState", {})
        destination = trip_state.get("destination", {})
        
        # Check environments
        environments = trip_request.get("environments", [])
        if "beach" in environments:
            types["beach"] += 1
        if "mountains" in environments:
            types["mountain"] += 1
        if "city" in environments:
            types["city"] += 1
        if "countryside" in environments:
            types["countryside"] += 1
        
        # Check destination name for clues
        name = destination.get("name", "").lower()
        if any(word in name for word in ["island", "beach", "coast", "sea"]):
            types["coastal"] += 1
        if any(word in name for word in ["mountain", "alps", "peak"]):
            types["mountain"] += 1
    
    return dict(types)

