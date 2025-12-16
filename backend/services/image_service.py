"""
Image service for fetching destination images from Unsplash.
Completely separate from agents - pure utility function.
"""
import logging
import requests
from typing import Optional
from urllib.parse import quote
import re
import unicodedata

from config import Config

logger = logging.getLogger(__name__)

# Default fallback image if Unsplash fails
DEFAULT_IMAGE_URL = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800"


def extract_city_name(destination_name: str) -> str:
    """
    Extract the main city name from a complex destination name.
    
    Examples:
        "Cancún / Riviera Maya (Tulum & Sian Ka'an)" -> "Cancun"
        "Bali (Ubud + Nusa Dua/Uluwatu)" -> "Bali"
        "Panama City (with trips to San Blas & Gamboa Rainforest)" -> "Panama City"
        "Mahé (Seychelles)" -> "Mahe"
    
    Args:
        destination_name: Full destination name
    
    Returns:
        Simplified city name for API queries
    """
    # Remove content in parentheses
    city = re.sub(r'\([^)]*\)', '', destination_name)
    
    # Remove content after slashes (but keep the first part)
    if '/' in city:
        city = city.split('/')[0].strip()
    
    # Remove common prefixes like "with trips to"
    city = re.sub(r'\s*with\s+.*$', '', city, flags=re.IGNORECASE)
    
    # Remove special characters and normalize
    city = re.sub(r'[&+]', '', city)
    
    # Remove extra whitespace
    city = ' '.join(city.split())
    
    # Remove accents and special characters for better API matching
    city = unicodedata.normalize('NFD', city)
    city = ''.join(c for c in city if unicodedata.category(c) != 'Mn')
    
    return city.strip()


def extract_activity_search_term(activity_name: str, description: str = "") -> str:
    """
    Extract a better search term for activity images from activity name and description.
    
    Examples:
        "Arrival + Check-in" -> "airplane"
        "Tapas dinner" -> "tapas"
        "Sunset photography" -> "sunset"
        "Museum visit" -> "museum"
    
    Args:
        activity_name: Activity name
        description: Optional activity description
    
    Returns:
        Search term for Unsplash
    """
    text = f"{activity_name} {description}".lower()
    
    # Map common activity keywords to better search terms
    keyword_mapping = {
        'arrival': 'airplane',
        'airport': 'airplane',
        'check-in': 'hotel lobby',
        'checkin': 'hotel lobby',
        'tapas': 'tapas',
        'dinner': 'restaurant food',
        'lunch': 'restaurant food',
        'breakfast': 'breakfast food',
        'sunset': 'sunset',
        'sunrise': 'sunrise',
        'photography': 'photography',
        'photo': 'photography',
        'hike': 'hiking trail',
        'hiking': 'hiking trail',
        'beach': 'beach',
        'museum': 'museum',
        'cathedral': 'cathedral',
        'church': 'church',
        'temple': 'temple',
        'market': 'market',
        'shopping': 'shopping',
        'snorkel': 'snorkeling',
        'diving': 'scuba diving',
        'swimming': 'swimming pool',
        'spa': 'spa',
        'wine': 'wine tasting',
        'coffee': 'coffee',
        'cafe': 'coffee shop',
        'viewpoint': 'scenic view',
        'view': 'scenic view',
        'monument': 'monument',
        'park': 'park',
        'garden': 'garden',
    }
    
    # Check for keywords in the text
    for keyword, search_term in keyword_mapping.items():
        if keyword in text:
            return search_term
    
    # If no keyword match, extract main words from activity name
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
    words = re.findall(r'\b\w+\b', activity_name.lower())
    meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    if meaningful_words:
        # Take first meaningful word or combine first two
        if len(meaningful_words) >= 2:
            return f"{meaningful_words[0]} {meaningful_words[1]}"
        return meaningful_words[0]
    
    # Fallback to first word of activity name
    first_word = activity_name.split()[0].lower() if activity_name else "travel"
    return first_word


def fetch_activity_image(activity_name: str, description: str = "") -> str:
    """
    Fetch an image for an activity from Unsplash API.
    
    Uses intelligent keyword extraction to find better search terms.
    
    Args:
        activity_name: Name of the activity (e.g., "Arrival + Check-in", "Tapas dinner")
        description: Optional activity description
    
    Returns:
        URL of the image, or default fallback if API call fails
    """
    if not Config.UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY not set, using default image")
        return DEFAULT_IMAGE_URL
    
    try:
        # Extract better search term from activity name
        search_term = extract_activity_search_term(activity_name, description)
        logger.debug(f"Searching Unsplash for activity '{activity_name}' using term '{search_term}'")
        
        # Use the same pattern as the working code - put params directly in URL
        api_key = Config.UNSPLASH_ACCESS_KEY.strip('"\'') if Config.UNSPLASH_ACCESS_KEY else None
        if not api_key:
            logger.warning("UNSPLASH_ACCESS_KEY is empty after stripping quotes")
            return DEFAULT_IMAGE_URL
        
        encoded_term = quote(search_term)
        url = f"https://api.unsplash.com/search/photos?query={encoded_term}&client_id={api_key}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Get first image URL
        if not data.get("results"):
            logger.warning(f"No photos found for activity '{activity_name}' (search term: '{search_term}')")
            return DEFAULT_IMAGE_URL

        image_url = data["results"][0]["urls"]["regular"]
        logger.info(f"Fetched Unsplash image for activity '{activity_name}': {image_url[:50]}...")
        return image_url
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error(f"Unauthorized: Invalid UNSPLASH_ACCESS_KEY. Check your API key.")
        elif e.response.status_code == 403:
            logger.error(f"Forbidden: API key may have rate limit exceeded or insufficient permissions.")
        else:
            logger.error(f"HTTP error fetching activity image: {e.response.status_code}")
        return DEFAULT_IMAGE_URL
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error fetching activity image: {e}")
        return DEFAULT_IMAGE_URL
    except KeyError as e:
        logger.warning(f"Error parsing Unsplash response for activity: Missing key {e}")
        return DEFAULT_IMAGE_URL
    except Exception as e:
        logger.warning(f"Unexpected error loading activity image: {e}")
        return DEFAULT_IMAGE_URL


def fetch_destination_image(city: str) -> str:
    """
    Fetch a destination image from Unsplash API.
    
    Args:
        city: Name of the city/destination (e.g., "Zurich", "Paris")
    
    Returns:
        URL of the image, or default fallback if API call fails
    """
    if not Config.UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY not set, using default image")
        return DEFAULT_IMAGE_URL
    
    try:
        # Extract simplified city name for better search results
        simple_city = extract_city_name(city)
        logger.debug(f"Searching Unsplash for '{simple_city}' (from '{city}')")
        
        # Use the same pattern as the working code - put params directly in URL
        # Properly URL-encode the city name and ensure API key has no quotes
        api_key = Config.UNSPLASH_ACCESS_KEY.strip('"\'') if Config.UNSPLASH_ACCESS_KEY else None
        if not api_key:
            logger.warning("UNSPLASH_ACCESS_KEY is empty after stripping quotes")
            return DEFAULT_IMAGE_URL
        
        encoded_city = quote(simple_city)
        url = f"https://api.unsplash.com/search/photos?query={encoded_city}&client_id={api_key}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Get first image URL
        if not data.get("results"):
            logger.warning(f"No photos found for '{city}'")
            return DEFAULT_IMAGE_URL

        image_url = data["results"][0]["urls"]["regular"]
        logger.info(f"Fetched Unsplash image for {city}: {image_url[:50]}...")
        return image_url
        
    except requests.exceptions.HTTPError as e:
        # More detailed error logging for HTTP errors
        if e.response.status_code == 401:
            logger.error(f"Unauthorized: Invalid UNSPLASH_ACCESS_KEY. Check your API key.")
        elif e.response.status_code == 403:
            logger.error(f"Forbidden: API key may have rate limit exceeded or insufficient permissions.")
        else:
            logger.error(f"HTTP error fetching image for {city}: {e.response.status_code} - {e.response.text[:200]}")
        return DEFAULT_IMAGE_URL
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error fetching image for {city}: {e}")
        return DEFAULT_IMAGE_URL
    except KeyError as e:
        logger.warning(f"Error parsing Unsplash response for {city}: Missing key {e}")
        return DEFAULT_IMAGE_URL
    except Exception as e:
        logger.warning(f"Unexpected error loading image for {city}: {e}")
        return DEFAULT_IMAGE_URL


def extract_transport_search_term(transport_name: str, transport_type: str = "") -> str:
    """
    Extract a better search term for transport images from transport name and type.
    
    Examples:
        "Private Taxi" -> "taxi"
        "Premium Uber" -> "uber car"
        "Airport Bus" -> "airport bus"
        "ATV Rental" -> "atv"
        "Scenic Walk" -> "walking path"
    
    Args:
        transport_name: Transport name
        transport_type: Transport type (taxi, uber, public, rental, walk)
    
    Returns:
        Search term for Unsplash
    """
    text = f"{transport_name} {transport_type}".lower()
    
    # Map transport types and keywords to better search terms
    keyword_mapping = {
        'taxi': 'taxi',
        'uber': 'uber car',
        'bus': 'bus',
        'airport bus': 'airport bus',
        'local bus': 'city bus',
        'public': 'public transport',
        'rental': 'car rental',
        'atv': 'atv',
        'scooter': 'scooter',
        'walk': 'walking path',
        'scenic walk': 'scenic walking path',
        'transfer': 'airport transfer',
        'included transfer': 'airport transfer',
        'car rental': 'car rental',
    }
    
    # Check for keywords in the text
    for keyword, search_term in keyword_mapping.items():
        if keyword in text:
            return search_term
    
    # Fallback: use transport type or first word
    if transport_type:
        return transport_type
    first_word = transport_name.split()[0].lower() if transport_name else "transport"
    return first_word


def fetch_transport_image(transport_name: str, transport_type: str = "") -> str:
    """
    Fetch an image for a transport option from Unsplash API.
    
    Args:
        transport_name: Name of the transport (e.g., "Private Taxi", "Airport Bus")
        transport_type: Optional transport type (taxi, uber, public, rental, walk)
    
    Returns:
        URL of the image, or default fallback if API call fails
    """
    if not Config.UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY not set, using default image")
        return DEFAULT_IMAGE_URL
    
    try:
        # Extract better search term from transport name
        search_term = extract_transport_search_term(transport_name, transport_type)
        logger.debug(f"Searching Unsplash for transport '{transport_name}' using term '{search_term}'")
        
        api_key = Config.UNSPLASH_ACCESS_KEY.strip('"\'') if Config.UNSPLASH_ACCESS_KEY else None
        if not api_key:
            logger.warning("UNSPLASH_ACCESS_KEY is empty after stripping quotes")
            return DEFAULT_IMAGE_URL
        
        encoded_term = quote(search_term)
        url = f"https://api.unsplash.com/search/photos?query={encoded_term}&client_id={api_key}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            logger.warning(f"No photos found for transport '{transport_name}' (search term: '{search_term}')")
            return DEFAULT_IMAGE_URL

        image_url = data["results"][0]["urls"]["regular"]
        logger.info(f"Fetched Unsplash image for transport '{transport_name}': {image_url[:50]}...")
        return image_url
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error(f"Unauthorized: Invalid UNSPLASH_ACCESS_KEY. Check your API key.")
        elif e.response.status_code == 403:
            logger.error(f"Forbidden: API key may have rate limit exceeded or insufficient permissions.")
        else:
            logger.error(f"HTTP error fetching transport image: {e.response.status_code} - {e.response.text[:200]}")
        return DEFAULT_IMAGE_URL
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error fetching transport image: {e}")
        return DEFAULT_IMAGE_URL
    except KeyError as e:
        logger.warning(f"Error parsing Unsplash response for transport: Missing key {e}")
        return DEFAULT_IMAGE_URL
    except Exception as e:
        logger.warning(f"Unexpected error fetching transport image: {e}")
        return DEFAULT_IMAGE_URL
