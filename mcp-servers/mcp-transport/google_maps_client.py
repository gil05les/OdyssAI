"""
Google Maps API client for directions and geocoding.
Handles errors gracefully and returns structured responses.
"""
import os
import requests
from typing import Dict, Any, Optional, Tuple
from logger import get_logger

logger = get_logger("google_maps_client")


class GoogleMapsClient:
    """Client for Google Maps API."""
    
    def __init__(self):
        """Initialize the Google Maps client."""
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not found in environment")
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """
        Geocode an address to get coordinates.
        
        Args:
            address: Address or place name to geocode
        
        Returns:
            Dict with success, data/error, and source fields
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Google Maps API key not configured",
                "fallback_hint": "Use approximate coordinates or city center"
            }
        
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                "address": address,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK" or not data.get("results"):
                error_msg = data.get("error_message", f"Geocoding failed: {data.get('status')}")
                logger.warning(f"Geocoding failed for '{address}': {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "fallback_hint": f"Address '{address}' could not be geocoded. Use city center coordinates."
                }
            
            result = data["results"][0]
            location = result["geometry"]["location"]
            
            return {
                "success": True,
                "source": "google_maps",
                "data": {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "formatted_address": result.get("formatted_address", address),
                    "place_id": result.get("place_id")
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding request failed: {e}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "fallback_hint": "Use approximate coordinates based on city name"
            }
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "fallback_hint": "Use approximate coordinates"
            }
    
    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        departure_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get directions between two locations.
        
        Args:
            origin: Origin address or coordinates
            destination: Destination address or coordinates
            mode: Travel mode (driving, walking, transit)
            departure_time: Optional departure time (for transit)
        
        Returns:
            Dict with success, data/error, and source fields
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Google Maps API key not configured",
                "fallback_hint": "Estimate based on distance: driving ~60km/h, walking ~5km/h, transit varies"
            }
        
        try:
            url = f"{self.base_url}/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "key": self.api_key,
                "alternatives": "false"
            }
            
            if mode == "transit" and departure_time:
                params["departure_time"] = departure_time
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK" or not data.get("routes"):
                error_msg = data.get("error_message", f"Directions failed: {data.get('status')}")
                logger.warning(f"Directions failed ({mode}): {error_msg}")
                
                # Provide helpful fallback hints
                if mode == "transit":
                    fallback = "Public transit may not be available. Estimate: $2-5 per trip, 30-60 min"
                elif mode == "walking":
                    fallback = "Estimate walking time: ~5km/h, distance needed for accurate estimate"
                else:
                    fallback = "Estimate driving time: ~60km/h in cities, ~100km/h on highways"
                
                return {
                    "success": False,
                    "error": error_msg,
                    "fallback_hint": fallback
                }
            
            route = data["routes"][0]
            leg = route["legs"][0]
            
            # Extract duration
            duration_seconds = leg["duration"]["value"]
            duration_text = leg["duration"]["text"]
            
            # Extract distance
            distance_meters = leg["distance"]["value"]
            distance_text = leg["distance"]["text"]
            
            # Extract steps for transit/walking
            steps = []
            if mode in ["transit", "walking"]:
                for step in leg.get("steps", []):
                    instruction = step.get("html_instructions", "").replace("<b>", "").replace("</b>", "")
                    steps.append(instruction)
            
            result = {
                "success": True,
                "source": "google_maps",
                "data": {
                    "duration_seconds": duration_seconds,
                    "duration_text": duration_text,
                    "distance_meters": distance_meters,
                    "distance_text": distance_text,
                    "mode": mode,
                    "steps": steps if steps else None
                }
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Directions request failed: {e}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "fallback_hint": f"Estimate for {mode}: calculate based on distance and typical speeds"
            }
        except Exception as e:
            logger.error(f"Directions error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "fallback_hint": "Use distance-based estimates"
            }

