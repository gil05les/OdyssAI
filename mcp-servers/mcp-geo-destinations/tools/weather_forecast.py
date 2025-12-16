"""
Get weather forecast for specific date range.
Fetches temperature data from OpenWeatherMap API for the given dates.
"""
import os
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from logger import get_logger


def get_weather_forecast(
    latitude: float,
    longitude: float,
    from_date: str,
    to_date: str,
    city_name: Optional[str] = None,
    request_timeout: int = 10
) -> Dict[str, Any]:
    """
    Get temperature range for a specific date range.
    
    Uses OpenWeatherMap One Call API 3.0 day_summary endpoint to fetch
    temperature data for each day in the date range and returns the min/max.
    
    Args:
        latitude: Latitude coordinate of the destination
        longitude: Longitude coordinate of the destination
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format (inclusive)
        city_name: Optional city name for display purposes
        request_timeout: Request timeout in seconds (default: 10)
    
    Returns:
        Dictionary with:
        - min_temp: Minimum temperature in Celsius across all dates
        - max_temp: Maximum temperature in Celsius across all dates
        - temp_range: Formatted string "min-max°C"
        - dates_analyzed: List of dates that were successfully fetched
    
    Example:
        Input: {
            "latitude": 38.7223,
            "longitude": -9.1393,
            "from_date": "2026-01-11",
            "to_date": "2026-01-18",
            "city_name": "Lisbon"
        }
        Output: {
            "min_temp": 12,
            "max_temp": 18,
            "temp_range": "12-18°C",
            "dates_analyzed": ["2026-01-11", "2026-01-12", ...]
        }
    """
    request_id = f"weather_forecast_{int(time.time() * 1000)}"
    logger = get_logger("get_weather_forecast", request_id)
    
    try:
        # Get API key from environment and strip quotes if present
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENWEATHERMAP_API_KEY environment variable not set. "
                "Please set it in your .env file or environment."
            )
        # Strip quotes if present (common issue with .env files)
        api_key = api_key.strip('"\'')
        
        # Parse dates
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError as e:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {from_date} or {to_date}") from e
        
        if to_date_obj < from_date_obj:
            raise ValueError(f"End date ({to_date}) cannot be before start date ({from_date})")
        
        logger.info(
            f"Fetching weather forecast for: {city_name or f'{latitude},{longitude}'} "
            f"from {from_date} to {to_date}"
        )
        
        # Collect all temperatures from the date range
        all_min_temps = []
        all_max_temps = []
        dates_analyzed = []
        current_date = from_date_obj
        
        # Iterate through each day in the range
        while current_date <= to_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.debug(f"Fetching weather data for {date_str}")
            
            # Use OpenWeatherMap One Call API 3.0 day summary endpoint
            url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"
            params = {
                'lat': latitude,
                'lon': longitude,
                'date': date_str,
                'appid': api_key,
                'units': 'metric'  # Use metric units (Celsius)
            }
            
            try:
                response = requests.get(url, params=params, timeout=request_timeout)
                response.raise_for_status()
                data = response.json()
                
                # Extract temperature data
                temp_data = data.get('temperature', {})
                min_temp = temp_data.get('min')
                max_temp = temp_data.get('max')
                
                if min_temp is not None and max_temp is not None:
                    all_min_temps.append(min_temp)
                    all_max_temps.append(max_temp)
                    dates_analyzed.append(date_str)
                    logger.debug(f"Got temperature for {date_str}: {min_temp}°C - {max_temp}°C")
                else:
                    logger.warning(f"No temperature data available for {date_str}")
                
                # Small delay to respect rate limits
                time.sleep(0.1)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # Return error message instead of raising - let the agent handle it gracefully
                    logger.warning("Invalid OpenWeatherMap API key. Weather data unavailable - agent should estimate temperatures.")
                    return {
                        'error': 'Weather API unavailable',
                        'message': 'OpenWeatherMap API key is invalid or missing. Please estimate temperatures based on location, season, and typical climate patterns for this destination.',
                        'destination': {
                            'city': city_name,
                            'coordinates': {
                                'latitude': latitude,
                                'longitude': longitude
                            }
                        },
                        'date_range': {
                            'from': from_date,
                            'to': to_date
                        },
                        'suggestion': 'Estimate temperature range based on the destination\'s typical climate for this time of year.'
                    }
                elif e.response.status_code == 429:
                    logger.warning(f"Rate limit hit for {date_str}, skipping...")
                    # Continue to next date
                elif e.response.status_code == 400:
                    logger.warning(f"Bad request for {date_str} (date may be too far in future/past), skipping...")
                    # Continue to next date
                else:
                    logger.warning(f"Could not fetch data for {date_str}: {e}")
                    # Continue to next date
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {date_str}: {e}")
                # Continue to next date
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Calculate overall min and max
        if not all_min_temps or not all_max_temps:
            # Return error message instead of raising - let the agent estimate
            logger.warning(f"Could not fetch temperature data for any dates in range {from_date} to {to_date}.")
            return {
                'error': 'Weather data unavailable',
                'message': f'Could not fetch temperature data for the date range {from_date} to {to_date}. Please estimate temperatures based on location, season, and typical climate patterns for this destination.',
                'destination': {
                    'city': city_name,
                    'coordinates': {
                        'latitude': latitude,
                        'longitude': longitude
                    }
                },
                'date_range': {
                    'from': from_date,
                    'to': to_date
                },
                'suggestion': 'Estimate temperature range based on the destination\'s typical climate for this time of year.'
            }
        
        overall_min = min(all_min_temps)
        overall_max = max(all_max_temps)
        
        # Format as "min-max°C"
        temp_range_str = f"{int(overall_min)}-{int(overall_max)}°C"
        
        total_days = (to_date_obj - from_date_obj).days + 1
        logger.info(
            f"Temperature range calculated: {temp_range_str} "
            f"({len(dates_analyzed)}/{total_days} dates)"
        )
        
        return {
            'destination': {
                'city': city_name,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'min_temp': int(overall_min),
            'max_temp': int(overall_max),
            'temp_range': temp_range_str,
            'dates_analyzed': dates_analyzed,
            'analysis_date': datetime.now().isoformat()
        }
        
    except ValueError as error:
        logger.error(f"Configuration error: {str(error)}")
        # Return error instead of raising - let agent estimate
        return {
            'error': 'Configuration error',
            'message': f'Weather API configuration error: {str(error)}. Please estimate temperatures based on location and season.',
            'destination': {
                'city': city_name,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'suggestion': 'Estimate temperature range based on the destination\'s typical climate for this time of year.'
        }
    except requests.exceptions.RequestException as error:
        logger.error(f"API request error: {str(error)}")
        # Return error instead of raising - let agent estimate
        return {
            'error': 'Weather API request failed',
            'message': f'Failed to fetch weather data: {str(error)}. Please estimate temperatures based on location and season.',
            'destination': {
                'city': city_name,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'suggestion': 'Estimate temperature range based on the destination\'s typical climate for this time of year.'
        }
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        # Return error instead of raising - let agent estimate
        return {
            'error': 'Weather API error',
            'message': f'Unexpected error fetching weather data: {str(error)}. Please estimate temperatures based on location and season.',
            'destination': {
                'city': city_name,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'suggestion': 'Estimate temperature range based on the destination\'s typical climate for this time of year.'
        }


