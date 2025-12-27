"""
Extract flight preferences from trip history.
Analyzes airlines, class, layovers, price sensitivity, and departure times.
"""
import time
from typing import Dict, Any, List, Optional
from collections import Counter
from db_client import PreferencesDBClient
from logger import get_logger


def get_flight_preferences(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Extract flight preferences from user's trip history.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with flight preferences or no_preference indicators
    """
    request_id = f"flight_prefs_{int(time.time() * 1000)}"
    logger = get_logger("flight_preferences", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        trips = client.get_user_trips(user_id)
        
        # Filter trips with flights
        flights = []
        for trip in trips:
            trip_data = trip.get("trip_data", {})
            trip_state = trip_data.get("tripState", {})
            flight = trip_state.get("flight")
            if flight:
                flights.append(flight)
        
        if len(flights) < 3:
            return {
                "user_id": user_id,
                "trip_count": len(trips),
                "flights_count": len(flights),
                "has_preference": False,
                "reason": f"Insufficient data: only {len(flights)} flight(s) booked. Need at least 3 flights to establish preferences.",
                "preferences": None
            }
        
        # Aggregate flight data
        airlines = Counter()
        classes = Counter()
        stops_counts = Counter()
        prices = []
        departure_times = []
        
        for flight in flights:
            # Airline
            airline = flight.get("airline") or flight.get("airlineCode")
            if airline:
                airlines[airline] += 1
            
            # Class
            flight_class = flight.get("class")
            if flight_class:
                classes[flight_class] += 1
            
            # Stops
            stops = flight.get("stops", 0)
            stops_counts[stops] += 1
            
            # Price
            price = flight.get("price")
            if price:
                prices.append(price)
            
            # Departure time
            dep_time = flight.get("departureTime")
            if dep_time:
                departure_times.append(dep_time)
        
        # Analyze layover preference
        direct_count = stops_counts.get(0, 0)
        one_stop_count = stops_counts.get(1, 0)
        total = len(flights)
        
        if direct_count / total >= 0.7:
            layover_pref = "direct"
        elif (direct_count + one_stop_count) / total >= 0.7:
            layover_pref = "1_stop_ok"
        else:
            layover_pref = "no_preference"
        
        # Analyze price sensitivity
        if prices:
            avg_price = sum(prices) / len(prices)
            if avg_price < 500:
                price_sensitivity = "budget"
            elif avg_price < 1500:
                price_sensitivity = "mid_range"
            else:
                price_sensitivity = "premium"
        else:
            price_sensitivity = "no_preference"
        
        # Analyze departure time preference
        time_pref = _analyze_departure_times(departure_times)
        
        # Check variance in choices
        has_preference = (
            len(airlines) < len(flights) * 0.7 or  # Not all unique airlines
            len(classes) < len(flights) * 0.7 or   # Not all unique classes
            layover_pref != "no_preference"
        )
        
        preferences = {
            "preferred_airlines": dict(airlines.most_common(10)),
            "preferred_class": dict(classes.most_common(5)),
            "layover_preference": layover_pref,
            "price_sensitivity": price_sensitivity,
            "avg_price": round(avg_price, 2) if prices else None,
            "departure_time_preference": time_pref,
            "direct_flight_ratio": round(direct_count / total, 2) if total > 0 else 0
        }
        
        return {
            "user_id": user_id,
            "trip_count": len(trips),
            "flights_count": len(flights),
            "has_preference": has_preference,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error extracting flight preferences: {e}", exc_info=True)
        raise Exception(f"Failed to extract flight preferences: {str(e)}")


def _analyze_departure_times(departure_times: List[str]) -> str:
    """
    Analyze departure time patterns.
    Returns: "morning" | "afternoon" | "evening" | "red_eye" | "no_preference"
    """
    if not departure_times:
        return "no_preference"
    
    time_counts = {"morning": 0, "afternoon": 0, "evening": 0, "red_eye": 0}
    
    for time_str in departure_times:
        try:
            # Parse time string (format: "HH:MM" or "HH:MM:SS")
            parts = time_str.split(":")
            hour = int(parts[0])
            
            if 6 <= hour < 12:
                time_counts["morning"] += 1
            elif 12 <= hour < 18:
                time_counts["afternoon"] += 1
            elif 18 <= hour < 24:
                time_counts["evening"] += 1
            else:  # 0-6
                time_counts["red_eye"] += 1
        except (ValueError, IndexError):
            continue
    
    # Find most common
    if not any(time_counts.values()):
        return "no_preference"
    
    most_common = max(time_counts.items(), key=lambda x: x[1])
    total = sum(time_counts.values())
    
    # Only return preference if it's at least 40% of flights
    if most_common[1] / total >= 0.4:
        return most_common[0]
    
    return "no_preference"

