"""
Uber API client for ride estimates.
Handles errors gracefully and returns structured responses.

NOTE: Uber API integration is currently disabled as we were unable to obtain
an Uber API key. This client always returns a graceful error that triggers
LLM fallback for generating ride estimates based on knowledge.
"""
import os
import requests
from typing import Dict, Any, Optional
from logger import get_logger

logger = get_logger("uber_client")


class UberClient:
    """
    Client for Uber API.
    
    NOTE: Currently disabled - Uber API key was not obtainable.
    Always returns graceful error to trigger LLM fallback.
    """
    
    def __init__(self):
        """Initialize the Uber client."""
        # Uber API integration disabled - no API key available
        self.client_id = None
        self.client_secret = None
        self.server_token = None
        self.base_url = "https://api.uber.com/v1.2"
        
        logger.info("Uber API integration disabled - using LLM fallback for ride estimates")
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth access token using client credentials.
        
        Returns:
            Access token or None if authentication fails
        """
        if not self.client_id or not self.client_secret:
            return None
        
        try:
            url = "https://login.uber.com/oauth/v2/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "estimates"
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            return token_data.get("access_token")
            
        except Exception as e:
            logger.error(f"Failed to get Uber access token: {e}")
            return None
    
    def get_estimate(
        self,
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float
    ) -> Dict[str, Any]:
        """
        Get price and time estimates for a ride.
        
        NOTE: Uber API integration is disabled. This method always returns
        a graceful error that triggers LLM fallback for generating estimates.
        
        Args:
            start_latitude: Starting latitude
            start_longitude: Starting longitude
            end_latitude: Destination latitude
            end_longitude: Destination longitude
        
        Returns:
            Dict with success=False, error message, and fallback_hint for LLM
        """
        # Uber API integration disabled - always return graceful error for LLM fallback
        logger.info("Uber API not available - returning graceful error for LLM fallback")
        
        # Calculate approximate distance for better LLM estimates
        # Simple haversine distance calculation (rough estimate)
        import math
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(start_latitude)
        lat2_rad = math.radians(end_latitude)
        delta_lat = math.radians(end_latitude - start_latitude)
        delta_lon = math.radians(end_longitude - start_longitude)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c
        
        # Provide helpful fallback hint with distance context
        return {
            "success": False,
            "error": "Uber API integration unavailable (API key not obtainable)",
            "fallback_hint": f"Uber API not available. Estimate ride fare for ~{distance_km:.1f}km: "
                           f"Typical taxi/ride-share: ~$2-3/km + $3-5 base fare. "
                           f"For {distance_km:.1f}km: approximately ${(distance_km * 2.5 + 4):.0f}-${(distance_km * 3 + 5):.0f}. "
                           f"Duration: ~{int(distance_km * 1.5)}-{int(distance_km * 2)} minutes in city traffic."
        }
        
        try:
            # Get price estimates
            url = f"{self.base_url}/estimates/price"
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json"
            }
            params = {
                "start_latitude": start_latitude,
                "start_longitude": start_longitude,
                "end_latitude": end_latitude,
                "end_longitude": end_longitude
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Handle different error cases
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "Uber API authentication failed",
                    "fallback_hint": "Estimate taxi fare: ~$2-3/km + $3-5 base fare"
                }
            
            if response.status_code == 403:
                return {
                    "success": False,
                    "error": "Uber API access forbidden (may not be available in this region)",
                    "fallback_hint": "Uber may not operate here. Estimate taxi: ~$2-3/km + base fare"
                }
            
            if response.status_code == 404:
                return {
                    "success": False,
                    "error": "Uber service not available for this route",
                    "fallback_hint": "Uber unavailable. Estimate taxi: ~$2-3/km + $3-5 base fare"
                }
            
            response.raise_for_status()
            data = response.json()
            
            if "prices" not in data or not data["prices"]:
                return {
                    "success": False,
                    "error": "No Uber estimates available for this route",
                    "fallback_hint": "Estimate taxi fare: ~$2-3/km + $3-5 base fare"
                }
            
            # Get time estimates
            time_url = f"{self.base_url}/estimates/time"
            time_response = requests.get(
                time_url,
                headers=headers,
                params={
                    "start_latitude": start_latitude,
                    "start_longitude": start_longitude
                },
                timeout=10
            )
            
            time_estimate = None
            if time_response.status_code == 200:
                time_data = time_response.json()
                if time_data.get("times") and len(time_data["times"]) > 0:
                    time_estimate = time_data["times"][0].get("estimate", None)
            
            # Use the cheapest available option (usually UberX)
            prices = data["prices"]
            best_price = min(prices, key=lambda x: x.get("low_estimate", float('inf')))
            
            low_estimate = best_price.get("low_estimate")
            high_estimate = best_price.get("high_estimate")
            currency = best_price.get("currency_code", "USD")
            display_name = best_price.get("display_name", "Uber")
            
            # Format price range
            if low_estimate and high_estimate:
                price_range = f"{currency} {low_estimate}-{high_estimate}"
                avg_price = (low_estimate + high_estimate) / 2
            elif low_estimate:
                price_range = f"{currency} {low_estimate}+"
                avg_price = low_estimate
            else:
                price_range = None
                avg_price = None
            
            return {
                "success": True,
                "source": "uber",
                "data": {
                    "price_range": price_range,
                    "price": avg_price,
                    "currency": currency,
                    "duration_estimate_seconds": time_estimate,
                    "display_name": display_name,
                    "product_id": best_price.get("product_id")
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Uber API request failed: {e}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "fallback_hint": "Estimate taxi fare: ~$2-3/km + $3-5 base fare. Calculate based on distance."
            }
        except Exception as e:
            logger.error(f"Uber API error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "fallback_hint": "Estimate taxi fare: ~$2-3/km + $3-5 base fare"
            }

