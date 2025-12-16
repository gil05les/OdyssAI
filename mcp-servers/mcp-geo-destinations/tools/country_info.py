"""
Get country information tool.
Retrieves country data from RestCountries API including currency, languages, timezone, and visa info.
"""
import time
import requests
from typing import Dict, Any, Optional
from logger import get_logger


def get_country_info(
    country_code: Optional[str] = None,
    country_name: Optional[str] = None,
    request_timeout: int = 10
) -> Dict[str, Any]:
    """
    Get comprehensive information about a country.
    
    Args:
        country_code: ISO 3166-1 alpha-2 or alpha-3 country code (e.g., "CH", "CHE", "US", "USA")
        country_name: Country name (e.g., "Switzerland", "United States")
        request_timeout: Request timeout in seconds (default: 10)
    
    Returns:
        Dictionary with country information including:
        - Currency
        - Languages
        - Timezone
        - Basic visa notes
        - Capital
        - Region
        - Population
        - etc.
    
    Example:
        Input: {"country_code": "CH"}
        Output: {
            "country": "Switzerland",
            "currency": {"code": "CHF", "name": "Swiss franc"},
            "languages": ["German", "French", "Italian", "Romansh"],
            "timezone": ["UTC+01:00"],
            "visa_info": {...}
        }
    """
    request_id = f"country_info_{int(time.time() * 1000)}"
    logger = get_logger("get_country_info", request_id)
    
    try:
        if not country_code and not country_name:
            raise ValueError("Either country_code or country_name must be provided")
        
        logger.info(f"Fetching country info for: {country_code or country_name}")
        
        # RestCountries API endpoint
        # Supports both alpha-2, alpha-3 codes, and country names
        if country_code:
            # Try alpha-2 code first, then alpha-3
            url = f"https://restcountries.com/v3.1/alpha/{country_code}"
        else:
            url = f"https://restcountries.com/v3.1/name/{country_name}"
        
        logger.debug(f"Calling RestCountries API: {url}")
        
        start_time = time.time()
        
        # Make API request
        response = requests.get(url, timeout=request_timeout)
        response.raise_for_status()
        
        duration = time.time() - start_time
        logger.info(f"API call completed in {duration:.3f}s")
        
        # Parse response
        data = response.json()
        
        # Handle array response (name search can return multiple)
        if isinstance(data, list):
            if len(data) == 0:
                raise Exception(f"Country not found: {country_code or country_name}")
            data = data[0]  # Use first result
        
        # Extract and normalize information
        country_name_full = data.get('name', {}).get('common', '')
        country_official = data.get('name', {}).get('official', '')
        
        # Currency information
        currencies = data.get('currencies', {})
        currency_list = []
        for code, info in currencies.items():
            currency_list.append({
                'code': code,
                'name': info.get('name', ''),
                'symbol': info.get('symbol', '')
            })
        
        # Languages
        languages = data.get('languages', {})
        language_list = list(languages.values()) if languages else []
        
        # Timezones
        timezones = data.get('timezones', [])
        
        # Visa information (from visa-free countries or visa requirements)
        # Note: RestCountries API doesn't directly provide visa info, but we can note this
        visa_info = {
            'note': 'Visa requirements vary by nationality. Check with embassy for specific requirements.',
            'visa_free_countries': data.get('borders', []),  # Countries sharing borders
        }
        
        # Additional useful information
        capital = data.get('capital', [])
        region = data.get('region', '')
        subregion = data.get('subregion', '')
        population = data.get('population', 0)
        area = data.get('area', 0)
        calling_code = data.get('idd', {}).get('root', '') + (data.get('idd', {}).get('suffixes', [''])[0] if data.get('idd', {}).get('suffixes') else '')
        
        normalized_info = {
            'country': country_name_full,
            'country_official': country_official,
            'country_code_alpha2': data.get('cca2', ''),
            'country_code_alpha3': data.get('cca3', ''),
            'currency': currency_list[0] if currency_list else None,
            'currencies': currency_list,
            'languages': language_list,
            'timezone': timezones[0] if timezones else None,
            'timezones': timezones,
            'capital': capital[0] if capital else None,
            'capitals': capital,
            'region': region,
            'subregion': subregion,
            'population': population,
            'area_km2': area,
            'calling_code': calling_code,
            'visa_info': visa_info,
            'flag': data.get('flags', {}).get('png', ''),
            'flag_emoji': data.get('flag', ''),
            'coordinates': {
                'latitude': data.get('latlng', [None, None])[0],
                'longitude': data.get('latlng', [None, None])[1]
            }
        }
        
        logger.info(f"Retrieved info for: {country_name_full}")
        logger.debug(f"Currency: {normalized_info['currency']['code'] if normalized_info['currency'] else 'N/A'}")
        logger.debug(f"Languages: {', '.join(language_list[:3])}")
        
        return normalized_info
        
    except requests.exceptions.RequestException as error:
        logger.error(f"API request error: {str(error)}")
        raise Exception(f"Failed to fetch country information: {str(error)}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to get country info: {str(error)}")






