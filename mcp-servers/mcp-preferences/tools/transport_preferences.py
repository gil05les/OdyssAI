"""
Extract transport preferences from trip history.
Analyzes transport modes, price sensitivity, and walk willingness.
"""
import time
from typing import Dict, Any, List, Optional
from collections import Counter
from db_client import PreferencesDBClient
from logger import get_logger


def get_transport_preferences(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Extract transport preferences from user's trip history.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with transport preferences or no_preference indicators
    """
    request_id = f"transport_prefs_{int(time.time() * 1000)}"
    logger = get_logger("transport_preferences", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        trips = client.get_user_trips(user_id)
        
        # Collect all transport selections
        transport_selections = []
        
        for trip in trips:
            trip_data = trip.get("trip_data", {})
            trip_state = trip_data.get("tripState", {})
            transport = trip_state.get("transport", {})
            
            # Transport can be a dict of leg_id -> TransportOption
            if isinstance(transport, dict):
                for leg_id, option in transport.items():
                    if option:  # Not null
                        transport_selections.append(option)
            elif isinstance(transport, list):
                transport_selections.extend(transport)
        
        if len(transport_selections) < 5:
            return {
                "user_id": user_id,
                "trip_count": len(trips),
                "transport_selections_count": len(transport_selections),
                "has_preference": False,
                "reason": f"Insufficient data: only {len(transport_selections)} transport selection(s). Need at least 5 selections to establish preferences.",
                "preferences": None
            }
        
        # Aggregate transport data
        modes = Counter()
        prices = []
        walk_count = 0
        
        for selection in transport_selections:
            # Transport type/mode
            transport_type = selection.get("type")
            if transport_type:
                modes[transport_type] += 1
                if transport_type == "walk":
                    walk_count += 1
            
            # Price
            price = selection.get("price")
            if price and price > 0:
                prices.append(price)
        
        # Calculate walk willingness
        walk_willingness = round(walk_count / len(transport_selections), 2) if transport_selections else 0
        
        # Determine price sensitivity
        public_count = modes.get("public", 0)
        walk_count_total = modes.get("walk", 0)
        taxi_count = modes.get("taxi", 0)
        uber_count = modes.get("uber", 0)
        total = len(transport_selections)
        
        budget_modes = public_count + walk_count_total
        convenience_modes = taxi_count + uber_count
        
        if budget_modes / total >= 0.6:
            price_sensitivity = "budget"
        elif convenience_modes / total >= 0.6:
            price_sensitivity = "convenience"
        else:
            price_sensitivity = "balanced"
        
        preferences = {
            "preferred_modes": dict(modes.most_common(10)),
            "price_sensitivity": price_sensitivity,
            "walk_willingness": walk_willingness,
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0
        }
        
        return {
            "user_id": user_id,
            "trip_count": len(trips),
            "transport_selections_count": len(transport_selections),
            "has_preference": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error extracting transport preferences: {e}", exc_info=True)
        raise Exception(f"Failed to extract transport preferences: {str(e)}")

