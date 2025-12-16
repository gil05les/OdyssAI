"""
Get best travel season tool.
Analyzes historical weather data from OpenWeatherMap to determine optimal travel periods.
"""
import os
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from logger import get_logger


def get_best_travel_season(
    latitude: float,
    longitude: float,
    city_name: Optional[str] = None,
    country_code: Optional[str] = None,
    months_to_analyze: int = 12,
    request_timeout: int = 10
) -> Dict[str, Any]:
    """
    Determine the best travel season for a destination based on historical weather data.
    
    Uses OpenWeatherMap API to analyze temperature, precipitation, and weather conditions
    across different months to identify optimal travel periods.
    
    Args:
        latitude: Latitude coordinate of the destination
        longitude: Longitude coordinate of the destination
        city_name: Optional city name for display purposes
        country_code: Optional country code for context
        months_to_analyze: Number of months to analyze (default: 12, for full year)
        request_timeout: Request timeout in seconds (default: 10)
    
    Returns:
        Dictionary with:
        - Best months to visit
        - Weather analysis by month
        - Temperature ranges
        - Precipitation patterns
        - Recommendations
    
    Example:
        Input: {
            "latitude": 38.7223,
            "longitude": -9.1393,
            "city_name": "Lisbon"
        }
        Output: {
            "best_months": ["May", "June", "September", "October"],
            "weather_by_month": {...},
            "recommendations": "..."
        }
    """
    request_id = f"travel_season_{int(time.time() * 1000)}"
    logger = get_logger("get_best_travel_season", request_id)
    
    try:
        # Get API key from environment
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENWEATHERMAP_API_KEY environment variable not set. "
                "Please set it in your .env file or environment."
            )
        
        logger.info(
            f"Analyzing best travel season for: {city_name or f'{latitude},{longitude}'}"
        )
        
        # Strategy: Sample historical data from the past year for each month
        # We'll query a representative date from each month to get average conditions
        current_date = datetime.now()
        month_data = {}
        
        # For each month, get historical data from the same month last year
        for month_offset in range(months_to_analyze):
            # Go back to the same month last year
            target_date = current_date - timedelta(days=365 - (month_offset * 30))
            target_date_str = target_date.strftime('%Y-%m-%d')
            
            month_name = target_date.strftime('%B')
            month_num = target_date.month
            
            logger.debug(f"Fetching weather data for {month_name} ({target_date_str})")
            
            # Use OpenWeatherMap One Call API 3.0 day summary endpoint
            # This provides aggregated daily weather data
            url = "https://api.openweathermap.org/data/3.0/onecall/day_summary"
            params = {
                'lat': latitude,
                'lon': longitude,
                'date': target_date_str,
                'appid': api_key,
                'units': 'metric'  # Use metric units (Celsius, mm)
            }
            
            try:
                response = requests.get(url, params=params, timeout=request_timeout)
                response.raise_for_status()
                data = response.json()
                
                # Extract key metrics
                temp_data = data.get('temperature', {})
                precipitation = data.get('precipitation', {})
                weather_main = data.get('weather', {}).get('main', '')
                
                month_data[month_num] = {
                    'month': month_name,
                    'month_number': month_num,
                    'temperature': {
                        'min': temp_data.get('min', 0),
                        'max': temp_data.get('max', 0),
                        'average': temp_data.get('day', 0)
                    },
                    'precipitation': {
                        'total_mm': precipitation.get('total', 0),
                        'probability': precipitation.get('probability', 0)
                    },
                    'weather_condition': weather_main,
                    'date_analyzed': target_date_str
                }
                
                # Small delay to respect rate limits
                time.sleep(0.1)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    raise Exception("Invalid OpenWeatherMap API key. Please check your OPENWEATHERMAP_API_KEY.")
                elif e.response.status_code == 429:
                    logger.warning(f"Rate limit hit for {month_name}, skipping...")
                    continue
                else:
                    logger.warning(f"Could not fetch data for {month_name}: {e}")
                    continue
            except Exception as e:
                logger.warning(f"Error fetching data for {month_name}: {e}")
                continue
        
        if not month_data:
            raise Exception("Could not fetch any weather data. Please check your API key and coordinates.")
        
        # Analyze the data to determine best months
        # Criteria: Moderate temperature (15-25°C ideal), low precipitation, good weather
        best_months = []
        month_scores = {}
        
        for month_num, data in month_data.items():
            temp_avg = data['temperature']['average']
            precip_total = data['precipitation']['total_mm']
            precip_prob = data['precipitation']['probability']
            
            # Scoring system
            score = 0
            
            # Temperature score (prefer 15-25°C)
            if 15 <= temp_avg <= 25:
                score += 10
            elif 10 <= temp_avg < 15 or 25 < temp_avg <= 30:
                score += 5
            elif 5 <= temp_avg < 10 or 30 < temp_avg <= 35:
                score += 2
            else:
                score -= 2
            
            # Precipitation score (lower is better)
            if precip_total < 50:  # Less than 50mm
                score += 5
            elif precip_total < 100:
                score += 2
            elif precip_total > 150:
                score -= 3
            
            # Precipitation probability (lower is better)
            if precip_prob < 0.2:  # Less than 20% chance
                score += 3
            elif precip_prob < 0.4:
                score += 1
            elif precip_prob > 0.6:
                score -= 2
            
            month_scores[month_num] = {
                'score': score,
                'month_name': data['month'],
                'data': data
            }
        
        # Sort by score and get top months
        sorted_months = sorted(
            month_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        # Get top 4-6 months as "best"
        best_count = min(6, len(sorted_months))
        best_months = [item[1]['month_name'] for item in sorted_months[:best_count]]
        
        # Build recommendations
        recommendations = []
        if best_months:
            recommendations.append(
                f"Best time to visit: {', '.join(best_months)}"
            )
        
        # Add seasonal insights
        avg_temp_by_season = {}
        for month_num, data in month_data.items():
            season = _get_season(month_num)
            if season not in avg_temp_by_season:
                avg_temp_by_season[season] = []
            avg_temp_by_season[season].append(data['temperature']['average'])
        
        for season, temps in avg_temp_by_season.items():
            avg_temp = sum(temps) / len(temps) if temps else 0
            recommendations.append(
                f"{season.capitalize()} average temperature: {avg_temp:.1f}°C"
            )
        
        logger.info(f"Analysis complete. Best months: {', '.join(best_months)}")
        
        return {
            'destination': {
                'city': city_name,
                'country_code': country_code,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'best_months': best_months,
            'best_months_detailed': [
                {
                    'month': month_scores[month_num]['month_name'],
                    'score': month_scores[month_num]['score'],
                    'temperature': month_scores[month_num]['data']['temperature'],
                    'precipitation': month_scores[month_num]['data']['precipitation']
                }
                for month_num, _ in sorted_months[:best_count]
            ],
            'weather_by_month': {
                month_data[month_num]['month']: {
                    'temperature': month_data[month_num]['temperature'],
                    'precipitation': month_data[month_num]['precipitation'],
                    'weather_condition': month_data[month_num]['weather_condition']
                }
                for month_num in sorted(month_data.keys())
            },
            'recommendations': recommendations,
            'analysis_date': datetime.now().isoformat()
        }
        
    except ValueError as error:
        logger.error(f"Configuration error: {str(error)}")
        raise
    except requests.exceptions.RequestException as error:
        logger.error(f"API request error: {str(error)}")
        raise Exception(f"Failed to fetch weather data: {str(error)}")
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        raise Exception(f"Failed to analyze travel season: {str(error)}")


def _get_season(month: int) -> str:
    """Get season name for a month (Northern Hemisphere)."""
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'






