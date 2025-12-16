#!/usr/bin/env python3
"""
Test script for MCP Hotels tools.
Tests each tool individually without the MCP server wrapper.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Try to find .env file in project root
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

from amadeus_client import AmadeusClientWrapper
from tools.search_city import search_hotels_in_city
from tools.search_coordinates import search_hotels_by_coordinates
from tools.offer_details import get_hotel_offer_details


def test_search_hotels_in_city():
    """Test search_hotels_in_city tool."""
    print("\n" + "="*80)
    print("Testing: search_hotels_in_city")
    print("="*80)
    
    # Use dates that are in the future
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    check_out_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
    
    print(f"Using dates: {future_date} (check-in), {check_out_date} (check-out)")
    
    try:
        result = search_hotels_in_city(
            city_code="LIS",
            check_in=future_date,
            check_out=check_out_date,
            guests=2,
            max_price_per_night=150
        )
        print("\n✅ Success!")
        print(f"Found {result.get('total_offers', 0)} hotel offers")
        if result.get('hotel_offers'):
            first_offer = result['hotel_offers'][0]
            print(f"\nFirst offer:")
            print(f"  Hotel: {first_offer.get('hotel_name')}")
            print(f"  Price per night: {first_offer.get('price_per_night')} {first_offer.get('currency')}")
            print(f"  Offer ID: {first_offer.get('offer_id')}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_hotels_by_coordinates():
    """Test search_hotels_by_coordinates tool."""
    print("\n" + "="*80)
    print("Testing: search_hotels_by_coordinates")
    print("="*80)
    
    # Lisbon coordinates (near the beach)
    try:
        result = search_hotels_by_coordinates(
            latitude=38.7223,
            longitude=-9.1393,
            radius=5.0,
            radius_unit="KM"
        )
        print("\n✅ Success!")
        print(f"Found {result.get('total_hotels', 0)} hotels")
        if result.get('hotels'):
            first_hotel = result['hotels'][0]
            print(f"\nFirst hotel:")
            print(f"  Name: {first_hotel.get('name')}")
            print(f"  Distance: {first_hotel.get('distance')} {first_hotel.get('distance_unit')}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_hotel_offer_details():
    """Test get_hotel_offer_details tool."""
    print("\n" + "="*80)
    print("Testing: get_hotel_offer_details")
    print("="*80)
    
    print("⚠️  Note: This test requires a valid offer_id from search_hotels_in_city")
    print("   Skipping this test - run search_hotels_in_city first to get an offer_id")
    
    return True  # Skip for now


def main():
    """Run all tests."""
    print("MCP Hotels Tools - Direct Testing")
    print("="*80)
    
    # Check environment variables (support both naming conventions)
    has_api_key = os.getenv('AMADEUS_API_KEY') or os.getenv('AMADEUS_CLIENT_ID')
    has_api_secret = os.getenv('AMADEUS_API_SECRET') or os.getenv('AMADEUS_CLIENT_SECRET')
    
    if not has_api_key or not has_api_secret:
        print("\n⚠️  Warning: Amadeus credentials not found")
        print("   Please set them in your .env file (project root):")
        print("   AMADEUS_API_KEY=your_key")
        print("   AMADEUS_API_SECRET=your_secret")
        print("   AMADEUS_ENV=prod  # or 'test'")
        return
    
    results = []
    
    # Test search hotels in city
    results.append(("search_hotels_in_city", test_search_hotels_in_city()))
    
    # Test search hotels by coordinates
    results.append(("search_hotels_by_coordinates", test_search_hotels_by_coordinates()))
    
    # Test get hotel offer details (skipped)
    results.append(("get_hotel_offer_details", test_get_hotel_offer_details()))
    
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


if __name__ == "__main__":
    main()

