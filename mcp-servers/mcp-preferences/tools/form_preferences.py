"""
Extract form preferences from trip history.
Analyzes traveler type, environments, climate, trip vibe, experiences, budget, etc.
"""
import time
from typing import Dict, Any, List, Optional
from collections import Counter
from db_client import PreferencesDBClient
from logger import get_logger


def get_form_preferences(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Extract form preferences from user's trip history.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with form preferences or no_preference indicators
    """
    request_id = f"form_prefs_{int(time.time() * 1000)}"
    logger = get_logger("form_preferences", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        trips = client.get_user_trips(user_id)
        
        if len(trips) < 2:
            return {
                "user_id": user_id,
                "trip_count": len(trips),
                "has_preference": False,
                "reason": f"Insufficient data: only {len(trips)} trip(s). Need at least 2 trips to establish preferences.",
                "preferences": None
            }
        
        # Aggregate data
        traveler_types = Counter()
        group_sizes = []
        environments = Counter()
        climates = Counter()
        trip_vibes = Counter()
        experiences = Counter()
        budgets = []
        distance_prefs = Counter()
        trip_purposes = Counter()
        accommodations = Counter()
        
        for trip in trips:
            trip_data = trip.get("trip_data", {})
            trip_request = trip_data.get("tripRequest", {})
            
            # Traveler type
            if trip_request.get("traveler_type"):
                traveler_types[trip_request["traveler_type"]] += 1
            
            # Group size
            if trip_request.get("group_size"):
                group_sizes.append(trip_request["group_size"])
            
            # Environments
            for env in trip_request.get("environments", []):
                environments[env] += 1
            
            # Climate
            if trip_request.get("climate"):
                climates[trip_request["climate"]] += 1
            
            # Trip vibe
            if trip_request.get("trip_vibe"):
                trip_vibes[trip_request["trip_vibe"]] += 1
            
            # Experiences
            for exp in trip_request.get("experiences", []):
                experiences[exp] += 1
            
            # Budget
            budget = trip_request.get("budget")
            if budget and isinstance(budget, list) and len(budget) == 2:
                budgets.append(budget)
            
            # Distance preference
            if trip_request.get("distance_preference"):
                distance_prefs[trip_request["distance_preference"]] += 1
            
            # Trip purpose
            if trip_request.get("trip_purpose"):
                trip_purposes[trip_request["trip_purpose"]] += 1
            
            # Accommodation
            if trip_request.get("accommodation"):
                accommodations[trip_request["accommodation"]] += 1
        
        # Build preferences with confidence checks
        total_trips = len(trips)
        
        def get_most_common(counter: Counter, threshold: float = 0.4) -> Optional[str]:
            """Get most common value if it exceeds threshold percentage."""
            if not counter:
                return None
            most_common = counter.most_common(1)[0]
            if most_common[1] / total_trips >= threshold:
                return most_common[0]
            return None
        
        preferences = {
            "traveler_type": get_most_common(traveler_types) or "no_preference",
            "avg_group_size": round(sum(group_sizes) / len(group_sizes), 1) if group_sizes else None,
            "environments": dict(environments.most_common(10)),
            "climate": get_most_common(climates) or "no_preference",
            "trip_vibe": get_most_common(trip_vibes) or "no_preference",
            "experiences": dict(experiences.most_common(15)),
            "budget_range": {
                "avg_min": int(sum(b[0] for b in budgets) / len(budgets)) if budgets else None,
                "avg_max": int(sum(b[1] for b in budgets) / len(budgets)) if budgets else None
            } if budgets else None,
            "distance_preference": get_most_common(distance_prefs) or "no_preference",
            "trip_purpose": get_most_common(trip_purposes) or "no_preference",
            "accommodation": get_most_common(accommodations) or "no_preference"
        }
        
        # Determine if we have meaningful preferences
        has_preference = (
            preferences["traveler_type"] != "no_preference" or
            preferences["climate"] != "no_preference" or
            preferences["trip_vibe"] != "no_preference" or
            len(preferences["environments"]) > 0 or
            len(preferences["experiences"]) > 0
        )
        
        return {
            "user_id": user_id,
            "trip_count": total_trips,
            "has_preference": has_preference,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error extracting form preferences: {e}", exc_info=True)
        raise Exception(f"Failed to extract form preferences: {str(e)}")

