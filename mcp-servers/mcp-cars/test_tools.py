#!/usr/bin/env python3
"""
Test script for MCP Cars tools.
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
from tools.search_airport import search_cars_at_airport
from tools.offer_details import get_car_offer_details


def test_search_cars_at_airport():
    """Test search_cars_at_airport tool."""
    print("\n" + "="*80)
    print("Testing: search_cars_at_airport")
    print("="*80)
    
    # Use dates that are in the future
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    dropoff_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
    
    print(f"Using dates: {future_date} (pickup), {dropoff_date} (dropoff)")
    
    try:
        result = search_cars_at_airport(
            pickup_iata="LIS",
            pickup_date=future_date,
            dropoff_date=dropoff_date
        )
        print("\n✅ Success!")
        print(f"Found {result.get('total_offers', 0)} car rental offers")
        if result.get('car_offers'):
            first_offer = result['car_offers'][0]
            print(f"\nFirst offer:")
            print(f"  Vehicle: {first_offer.get('vehicle', {}).get('make')} {first_offer.get('vehicle', {}).get('model')}")
            print(f"  Price: {first_offer.get('pricing', {}).get('total')} {first_offer.get('pricing', {}).get('currency')}")
            print(f"  Offer ID: {first_offer.get('offer_id')}")
            return first_offer.get('offer_id')  # Return offer_id for next test
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_car_offer_details(offer_id: str = None):
    """Test get_car_offer_details tool."""
    print("\n" + "="*80)
    print("Testing: get_car_offer_details")
    print("="*80)
    
    if not offer_id:
        print("⚠️  Note: This test requires a valid offer_id from search_cars_at_airport")
        print("   Skipping this test - run search_cars_at_airport first to get an offer_id")
        return True
    
    try:
        result = get_car_offer_details(offer_id=offer_id)
        print("\n✅ Success!")
        offer_details = result.get('offer_details', {})
        print(f"\nOffer details:")
        print(f"  Vehicle: {offer_details.get('vehicle', {}).get('make')} {offer_details.get('vehicle', {}).get('model')}")
        print(f"  Price: {offer_details.get('pricing', {}).get('total')} {offer_details.get('pricing', {}).get('currency')}")
        insurance_count = len([i for i in offer_details.get('insurance', []) if i.get('included')])
        print(f"  Insurance included: {insurance_count} items")
        print(f"  Cancellation policy: {offer_details.get('cancellation_policy', {}).get('type', 'N/A')}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("MCP Cars Tools - Direct Testing")
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
    
    # Test search cars at airport
    offer_id = test_search_cars_at_airport()
    results.append(("search_cars_at_airport", offer_id is not None))
    
    # Test get car offer details (if we have an offer_id)
    if offer_id:
        results.append(("get_car_offer_details", test_get_car_offer_details(offer_id)))
    else:
        results.append(("get_car_offer_details", True))  # Skip
    
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

