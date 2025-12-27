"""
Get full preference profile combining all preference types.
Provides a comprehensive summary for LLM consumption.
"""
import time
from typing import Dict, Any, Optional
from db_client import PreferencesDBClient
from logger import get_logger
from tools.form_preferences import get_form_preferences
from tools.destination_preferences import get_destination_preferences
from tools.flight_preferences import get_flight_preferences
from tools.hotel_preferences import get_hotel_preferences
from tools.itinerary_preferences import get_itinerary_preferences
from tools.transport_preferences import get_transport_preferences


def get_full_preference_profile(
    user_id: int,
    client: Optional[PreferencesDBClient] = None
) -> Dict[str, Any]:
    """
    Get comprehensive preference profile combining all preference types.
    
    Args:
        user_id: The user ID to analyze
        client: Optional database client instance
    
    Returns:
        Dictionary with all preferences combined and a natural language summary
    """
    request_id = f"full_profile_{int(time.time() * 1000)}"
    logger = get_logger("full_profile", request_id)
    
    try:
        if client is None:
            client = PreferencesDBClient()
        
        # Get all preference types
        form_prefs = get_form_preferences(user_id, client)
        dest_prefs = get_destination_preferences(user_id, client)
        flight_prefs = get_flight_preferences(user_id, client)
        hotel_prefs = get_hotel_preferences(user_id, client)
        itinerary_prefs = get_itinerary_preferences(user_id, client)
        transport_prefs = get_transport_preferences(user_id, client)
        
        # Determine overall confidence
        trip_count = form_prefs.get("trip_count", 0)
        if trip_count == 0:
            confidence = "insufficient"
        elif trip_count == 1:
            confidence = "insufficient"
        elif trip_count < 5:
            confidence = "low"
        elif trip_count < 10:
            confidence = "medium"
        else:
            confidence = "high"
        
        # Build summary
        summary_parts = []
        
        # Form preferences
        if form_prefs.get("has_preference"):
            form_data = form_prefs.get("preferences", {})
            if form_data.get("traveler_type") != "no_preference":
                summary_parts.append(f"Travels as {form_data['traveler_type']}")
            if form_data.get("trip_vibe") != "no_preference":
                summary_parts.append(f"prefers {form_data['trip_vibe']} trips")
            if form_data.get("environments"):
                top_envs = list(form_data["environments"].keys())[:2]
                summary_parts.append(f"enjoys {', '.join(top_envs)} environments")
        
        # Destination preferences
        if dest_prefs.get("has_preference"):
            dest_data = dest_prefs.get("preferences", {})
            if dest_data.get("favorite_countries"):
                top_countries = list(dest_data["favorite_countries"].keys())[:2]
                summary_parts.append(f"frequently visits {', '.join(top_countries)}")
        
        # Flight preferences
        if flight_prefs.get("has_preference"):
            flight_data = flight_prefs.get("preferences", {})
            if flight_data.get("preferred_airlines"):
                top_airline = list(flight_data["preferred_airlines"].keys())[0]
                summary_parts.append(f"prefers {top_airline} airlines")
            if flight_data.get("layover_preference") != "no_preference":
                summary_parts.append(f"prefers {flight_data['layover_preference']} flights")
        
        # Hotel preferences
        if hotel_prefs.get("has_preference"):
            hotel_data = hotel_prefs.get("preferences", {})
            if hotel_data.get("preferred_star_rating", {}).get("most_common"):
                stars = hotel_data["preferred_star_rating"]["most_common"]
                summary_parts.append(f"typically stays at {stars}-star hotels")
        
        # Itinerary preferences
        if itinerary_prefs.get("has_preference"):
            itinerary_data = itinerary_prefs.get("preferences", {})
            if itinerary_data.get("pace_preference") != "no_preference":
                summary_parts.append(f"prefers {itinerary_data['pace_preference']} pace")
        
        # Transport preferences
        if transport_prefs.get("has_preference"):
            transport_data = transport_prefs.get("preferences", {})
            if transport_data.get("price_sensitivity"):
                summary_parts.append(f"transport: {transport_data['price_sensitivity']} focused")
        
        # Build summary string
        if summary_parts:
            summary = ". ".join(summary_parts) + "."
        else:
            summary = "Limited preference data available."
        
        # Combine all preferences
        profile = {
            "user_id": user_id,
            "trip_count": trip_count,
            "confidence": confidence,
            "summary": summary,
            "form_preferences": form_prefs.get("preferences") if form_prefs.get("has_preference") else None,
            "destination_preferences": dest_prefs.get("preferences") if dest_prefs.get("has_preference") else None,
            "flight_preferences": flight_prefs.get("preferences") if flight_prefs.get("has_preference") else None,
            "hotel_preferences": hotel_prefs.get("preferences") if hotel_prefs.get("has_preference") else None,
            "itinerary_preferences": itinerary_prefs.get("preferences") if itinerary_prefs.get("has_preference") else None,
            "transport_preferences": transport_prefs.get("preferences") if transport_prefs.get("has_preference") else None
        }
        
        return profile
        
    except Exception as e:
        logger.error(f"Error building full preference profile: {e}", exc_info=True)
        raise Exception(f"Failed to build preference profile: {str(e)}")

