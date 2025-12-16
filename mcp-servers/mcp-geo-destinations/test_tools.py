#!/usr/bin/env python3
"""
Test script for MCP Geo Destinations tools.
Tests each tool individually without the MCP server wrapper.
"""
import os
import sys
import json
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    current_file = Path(__file__).resolve()
    env_path = current_file.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  .env file not found at {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed, .env file will not be loaded")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

from tools.country_info import get_country_info
from tools.travel_season import get_best_travel_season
from tools.points_of_interest import get_points_of_interest


def test_get_country_info():
    """Test get_country_info tool."""
    print("\n" + "="*80)
    print("Testing: get_country_info")
    print("="*80)
    
    try:
        result = get_country_info(country_code="CH")
        print("\n✅ Success!")
        print(f"Country: {result.get('country')}")
        print(f"Currency: {result.get('currency', {}).get('code') if result.get('currency') else 'N/A'}")
        print(f"Languages: {', '.join(result.get('languages', [])[:3])}")
        print(f"Timezone: {result.get('timezone')}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_best_travel_season():
    """Test get_best_travel_season tool."""
    print("\n" + "="*80)
    print("Testing: get_best_travel_season")
    print("="*80)
    
    # Check for API key
    if not os.getenv('OPENWEATHERMAP_API_KEY'):
        print("⚠️  OPENWEATHERMAP_API_KEY not set. Skipping this test.")
        print("   To test this tool, add OPENWEATHERMAP_API_KEY to your .env file")
        return True  # Skip, not a failure
    
    try:
        # Lisbon coordinates
        result = get_best_travel_season(
            latitude=38.7223,
            longitude=-9.1393,
            city_name="Lisbon"
        )
        print("\n✅ Success!")
        print(f"Best months: {', '.join(result.get('best_months', []))}")
        print(f"Total months analyzed: {len(result.get('weather_by_month', {}))}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_points_of_interest():
    """Test get_points_of_interest tool."""
    print("\n" + "="*80)
    print("Testing: get_points_of_interest")
    print("="*80)
    
    # Check for Amadeus credentials
    has_api_key = os.getenv('AMADEUS_API_KEY') or os.getenv('AMADEUS_CLIENT_ID')
    has_api_secret = os.getenv('AMADEUS_API_SECRET') or os.getenv('AMADEUS_CLIENT_SECRET')
    
    if not has_api_key or not has_api_secret:
        print("⚠️  Amadeus credentials not set. Skipping this test.")
        return True  # Skip, not a failure
    
    try:
        # Lisbon coordinates
        result = get_points_of_interest(
            latitude=38.7223,
            longitude=-9.1393,
            radius=5.0
        )
        print("\n✅ Success!")
        print(f"Found {result.get('total_pois', 0)} points of interest")
        if result.get('pois'):
            first_poi = result['pois'][0]
            print(f"First POI: {first_poi.get('name')} ({first_poi.get('category')})")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("MCP Geo Destinations Tools - Direct Testing")
    print("="*80)
    
    results = []
    
    # Test get country info (no API key needed)
    results.append(("get_country_info", test_get_country_info()))
    
    # Test get best travel season (needs OpenWeatherMap API key)
    results.append(("get_best_travel_season", test_get_best_travel_season()))
    
    # Test get points of interest (needs Amadeus credentials)
    results.append(("get_points_of_interest", test_get_points_of_interest()))
    
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    print("\n" + "="*80)
    print("Environment Variables Required:")
    print("="*80)
    print("1. OPENWEATHERMAP_API_KEY - Required for get_best_travel_season")
    print("   Get your free API key at: https://openweathermap.org/api")
    print()
    print("2. AMADEUS_API_KEY / AMADEUS_CLIENT_ID - Required for get_points_of_interest")
    print("   AMADEUS_API_SECRET / AMADEUS_CLIENT_SECRET - Required for get_points_of_interest")
    print("   Get credentials at: https://developers.amadeus.com/")
    print()
    print("3. get_country_info uses RestCountries API (no API key required)")


if __name__ == "__main__":
    main()






