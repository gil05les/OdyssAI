"""
Temperature service for predicting destination temperatures based on climate knowledge.
Uses seasonal patterns and geographical data instead of external weather APIs.
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Climate zones with typical temperature ranges by season
# Format: (winter_min, winter_max, summer_min, summer_max)
CLIMATE_DATA = {
    # Northern Hemisphere - Temperate Europe
    "switzerland": (-2, 5, 15, 28),
    "germany": (-1, 5, 16, 28),
    "france": (2, 10, 18, 30),
    "italy": (4, 12, 22, 32),
    "spain": (5, 15, 22, 35),
    "portugal": (8, 15, 20, 30),
    "greece": (6, 14, 24, 35),
    "croatia": (2, 10, 22, 32),
    "netherlands": (1, 7, 14, 24),
    "belgium": (1, 7, 14, 24),
    "austria": (-3, 4, 15, 27),
    "united kingdom": (3, 9, 14, 23),
    "ireland": (3, 9, 13, 20),
    "sweden": (-5, 2, 14, 24),
    "norway": (-6, 1, 12, 22),
    "finland": (-10, -2, 12, 22),
    "denmark": (0, 5, 14, 22),
    "poland": (-4, 2, 16, 26),
    "czech republic": (-3, 3, 15, 26),
    "hungary": (-2, 5, 18, 30),
    
    # Mediterranean
    "turkey": (4, 12, 22, 35),
    "cyprus": (10, 17, 24, 35),
    "malta": (10, 16, 24, 32),
    "morocco": (8, 18, 22, 38),
    "tunisia": (8, 16, 24, 36),
    "egypt": (10, 20, 26, 40),
    
    # Asia
    "japan": (2, 10, 22, 32),
    "south korea": (-4, 5, 22, 32),
    "china": (-5, 8, 24, 35),
    "thailand": (22, 32, 26, 36),
    "vietnam": (15, 25, 26, 35),
    "indonesia": (24, 32, 24, 32),
    "malaysia": (24, 32, 24, 32),
    "singapore": (24, 32, 24, 32),
    "philippines": (24, 32, 26, 34),
    "india": (12, 25, 28, 42),
    "sri lanka": (22, 30, 26, 32),
    "maldives": (26, 31, 27, 32),
    "united arab emirates": (14, 24, 30, 45),
    "qatar": (14, 24, 32, 45),
    "israel": (8, 16, 24, 34),
    
    # Americas
    "united states": (0, 15, 20, 35),  # Varies greatly
    "canada": (-15, 0, 15, 28),
    "mexico": (12, 25, 22, 35),
    "brazil": (18, 28, 22, 32),
    "argentina": (8, 18, 18, 28),  # Southern hemisphere inverted
    "chile": (5, 15, 15, 28),
    "peru": (12, 20, 18, 26),
    "colombia": (14, 24, 14, 24),  # Tropical, stable
    "costa rica": (18, 28, 20, 30),
    "cuba": (20, 28, 26, 34),
    "dominican republic": (22, 30, 26, 34),
    "jamaica": (22, 30, 26, 34),
    
    # Oceania
    "australia": (10, 22, 20, 35),  # Southern hemisphere
    "new zealand": (5, 14, 15, 25),
    "fiji": (22, 28, 24, 30),
    
    # Africa
    "south africa": (8, 18, 18, 28),  # Southern hemisphere
    "kenya": (14, 26, 16, 28),
    "tanzania": (18, 28, 20, 30),
    "namibia": (6, 22, 18, 32),
    "botswana": (6, 24, 20, 35),
    
    # Default for unknown locations
    "default": (10, 20, 20, 30),
}

# City-specific overrides for more accuracy
CITY_OVERRIDES = {
    "zurich": (-2, 5, 16, 28),
    "geneva": (0, 6, 17, 28),
    "barcelona": (8, 15, 22, 30),
    "madrid": (2, 12, 22, 36),
    "lisbon": (8, 15, 20, 30),
    "paris": (2, 8, 17, 28),
    "london": (4, 10, 15, 25),
    "rome": (5, 12, 22, 32),
    "milan": (0, 8, 20, 32),
    "venice": (0, 8, 20, 30),
    "amsterdam": (1, 7, 14, 24),
    "berlin": (-1, 5, 16, 28),
    "munich": (-3, 4, 15, 27),
    "vienna": (-2, 5, 17, 28),
    "prague": (-3, 3, 16, 27),
    "budapest": (-2, 5, 18, 30),
    "athens": (7, 14, 26, 35),
    "istanbul": (4, 10, 22, 32),
    "dubai": (15, 25, 32, 42),
    "tokyo": (2, 10, 24, 32),
    "bangkok": (22, 32, 26, 35),
    "bali": (24, 31, 24, 31),
    "singapore": (24, 32, 24, 32),
    "sydney": (10, 18, 20, 28),
    "melbourne": (8, 15, 18, 26),
    "auckland": (8, 15, 18, 24),
    "new york": (-2, 6, 22, 32),
    "los angeles": (10, 20, 18, 30),
    "miami": (16, 26, 26, 34),
    "cancun": (20, 28, 26, 34),
    "rio de janeiro": (20, 28, 26, 34),
    "buenos aires": (8, 16, 20, 30),
    "cape town": (8, 18, 16, 26),
    "marrakech": (6, 18, 24, 40),
    "cairo": (10, 20, 28, 38),
    "santorini": (10, 16, 24, 32),
    "reykjavik": (-2, 4, 10, 16),
    "oslo": (-6, 1, 14, 24),
    "stockholm": (-5, 2, 16, 26),
    "copenhagen": (0, 5, 15, 23),
    "dublin": (3, 9, 14, 20),
    "edinburgh": (1, 7, 12, 19),
    "nice": (6, 14, 22, 30),
    "monaco": (8, 14, 22, 28),
    "porto": (6, 14, 18, 28),
    "seville": (6, 16, 24, 38),
    "malaga": (8, 18, 22, 34),
    "valencia": (6, 16, 22, 32),
    "florence": (2, 12, 20, 34),
    "naples": (5, 14, 22, 32),
    "palermo": (8, 16, 24, 32),
    "dubrovnik": (6, 12, 22, 30),
    "split": (6, 12, 24, 32),
    "santorini": (10, 16, 24, 32),
    "mykonos": (10, 16, 24, 30),
    "crete": (10, 16, 24, 32),
}


def get_season_factor(month: int, is_southern_hemisphere: bool = False) -> float:
    """
    Get a factor from 0 (winter) to 1 (summer) based on month.
    Inverted for southern hemisphere.
    """
    # Northern hemisphere: Jan=0 (winter), Jul=1 (summer)
    # Define monthly factors
    factors = [0.0, 0.1, 0.25, 0.45, 0.65, 0.85, 1.0, 0.95, 0.75, 0.5, 0.25, 0.1]
    
    factor = factors[month - 1] if 1 <= month <= 12 else 0.5
    
    if is_southern_hemisphere:
        factor = 1.0 - factor
    
    return factor


def is_southern_hemisphere(country: str) -> bool:
    """Check if a country is in the southern hemisphere."""
    southern_countries = {
        "australia", "new zealand", "argentina", "chile", "south africa",
        "namibia", "botswana", "zimbabwe", "mozambique", "madagascar",
        "indonesia", "brazil", "peru", "bolivia", "paraguay", "uruguay"
    }
    return country.lower() in southern_countries


def estimate_temperature_range(
    city: str,
    country: Optional[str] = None,
    month: Optional[int] = None
) -> str:
    """
    Estimate temperature range for a destination based on climate knowledge.
    
    Args:
        city: City name (e.g., "Zurich", "Cancun")
        country: Optional country name for better matching
        month: Optional month (1-12) for seasonal adjustment. Defaults to current month.
    
    Returns:
        Temperature range string in format "min-max°C" (e.g., "15-25°C")
    """
    if month is None:
        month = datetime.now().month
    
    city_lower = city.lower().strip()
    country_lower = (country or "").lower().strip()
    
    # Try city-specific data first
    if city_lower in CITY_OVERRIDES:
        winter_min, winter_max, summer_min, summer_max = CITY_OVERRIDES[city_lower]
        logger.debug(f"Using city override for {city}")
    elif country_lower in CLIMATE_DATA:
        winter_min, winter_max, summer_min, summer_max = CLIMATE_DATA[country_lower]
        logger.debug(f"Using country data for {country}")
    else:
        # Try partial country match
        for key in CLIMATE_DATA:
            if key in country_lower or country_lower in key:
                winter_min, winter_max, summer_min, summer_max = CLIMATE_DATA[key]
                logger.debug(f"Using partial country match: {key}")
                break
        else:
            winter_min, winter_max, summer_min, summer_max = CLIMATE_DATA["default"]
            logger.debug(f"Using default climate data for {city}, {country}")
    
    # Get season factor
    southern = is_southern_hemisphere(country_lower) if country_lower else False
    factor = get_season_factor(month, southern)
    
    # Interpolate between winter and summer temperatures
    min_temp = int(round(winter_min + (summer_min - winter_min) * factor))
    max_temp = int(round(winter_max + (summer_max - winter_max) * factor))
    
    # Ensure min < max
    if min_temp > max_temp:
        min_temp, max_temp = max_temp, min_temp
    
    temp_range = f"{min_temp}-{max_temp}°C"
    logger.info(f"Estimated temperature for {city}, {country} (month {month}): {temp_range}")
    
    return temp_range


def fetch_temperature_range(city: str, country: Optional[str] = None) -> Optional[str]:
    """
    Get temperature range for a destination.
    Uses climate-based estimation instead of external APIs.
    
    Args:
        city: City name (e.g., "Zurich", "Cancun")
        country: Optional country name or code for better matching
    
    Returns:
        Temperature range string in format "min-max°C" (e.g., "15-25°C")
    """
    try:
        return estimate_temperature_range(city, country)
    except Exception as e:
        logger.warning(f"Error estimating temperature for {city}: {e}")
        return "15-25°C"  # Fallback to a reasonable default
