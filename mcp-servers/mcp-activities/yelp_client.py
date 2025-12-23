"""
Yelp API client wrapper with authentication, timeout, and logging.
"""
import os
import socket
from pathlib import Path
from typing import Any, Dict, Optional, List
import requests

# Set a default socket timeout to prevent API calls from hanging indefinitely
socket.setdefaulttimeout(30)  # 30 seconds timeout

# Load .env file if it exists (from project root)
try:
    from dotenv import load_dotenv
    # Try to find .env file in project root
    # This file is at: OdyssAI/mcp-servers/mcp-activities/yelp_client.py
    # .env is at: OdyssAI/.env
    # So we go up 3 levels: mcp-activities -> mcp-servers -> OdyssAI
    current_file = Path(__file__).resolve()
    env_path = current_file.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except (ImportError, NameError):
    # python-dotenv not installed or __file__ not available, skip loading .env
    pass

from logger import get_logger


# Yelp category mappings - maps user-friendly names to Yelp category aliases
YELP_CATEGORIES = {
    "restaurants": "restaurants",
    "bars": "bars",
    "coffee": "coffee",
    "hotels": "hotels",
    "attractions": "tours",  # Yelp uses "tours" for tourist attractions
    "museums": "museums",
    "parks": "parks",
    "tours": "tours",
    "nightlife": "nightlife",
    "shopping": "shopping",
    "beauty": "beautysvc",
    "fitness": "fitness",
    "arts": "arts",
    "food": "food",
    "active": "active",
}


class YelpClient:
    """Wrapper for Yelp Fusion API with enhanced logging and error handling."""
    
    YELP_API_BASE = "https://api.yelp.com/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Yelp client.
        
        Args:
            api_key: Yelp API key (defaults to YELP_API_KEY env var)
        """
        self.logger = get_logger("YELP_CLIENT")
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('YELP_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Yelp API key not provided. "
                "Set YELP_API_KEY environment variable."
            )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        self.logger.info("Yelp client initialized")
    
    def search_businesses(
        self,
        location: str,
        category: str = "restaurants",
        limit: int = 10,
        sort_by: str = "rating"
    ) -> Dict[str, Any]:
        """
        Search for businesses on Yelp.
        
        Args:
            location: City/location to search (e.g., "St. Gallen, Switzerland")
            category: Business category (restaurants, bars, museums, etc.)
            limit: Number of results to return (max 50)
            sort_by: Sort order - best_match, rating, review_count, distance
        
        Returns:
            Dictionary with businesses list and metadata
        """
        url = f"{self.YELP_API_BASE}/businesses/search"
        
        # Map category to Yelp category alias
        yelp_category = YELP_CATEGORIES.get(category.lower(), category)
        
        params = {
            "location": location,
            "limit": min(limit, 50),  # Yelp max is 50
            "sort_by": sort_by
        }
        
        # Handle special categories that work better with term search
        if category.lower() in ["museums", "attractions", "tours"]:
            params["term"] = category
            if yelp_category:
                params["categories"] = yelp_category
        else:
            params["categories"] = yelp_category
        
        self.logger.info(f"Searching Yelp: {location} - {category}")
        self.logger.debug(f"API params: {params}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 401:
                self.logger.error("Invalid Yelp API key")
                raise ValueError("Invalid Yelp API key")
            elif response.status_code == 403:
                self.logger.error("Access forbidden - check API key permissions")
                raise PermissionError("Yelp API access forbidden")
            
            response.raise_for_status()
            data = response.json()
            
            businesses = data.get("businesses", [])
            total = data.get("total", 0)
            
            self.logger.info(f"Found {len(businesses)} businesses (total: {total})")
            
            return {
                "businesses": businesses,
                "total": total,
                "region": data.get("region", {})
            }
            
        except requests.exceptions.Timeout:
            self.logger.error("Yelp API request timed out")
            raise TimeoutError("Yelp API request timed out after 30 seconds")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Yelp API HTTP error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Yelp API request error: {e}")
            raise
    
    def get_business_details(self, business_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific business.
        
        Args:
            business_id: Yelp business ID
        
        Returns:
            Dictionary with business details
        """
        url = f"{self.YELP_API_BASE}/businesses/{business_id}"
        
        self.logger.info(f"Getting business details: {business_id}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get business details: {e}")
            raise
    
    @staticmethod
    def get_available_categories() -> Dict[str, str]:
        """Get available Yelp category mappings."""
        return {
            "restaurants": "Restaurants",
            "bars": "Bars",
            "coffee": "Coffee & Tea",
            "hotels": "Hotels",
            "attractions": "Tourist Attractions",
            "museums": "Museums",
            "parks": "Parks",
            "tours": "Tours",
            "nightlife": "Nightlife",
            "shopping": "Shopping",
            "beauty": "Beauty & Spas",
            "fitness": "Fitness & Active Life",
            "arts": "Arts & Entertainment",
            "food": "Food",
            "active": "Active Life"
        }

