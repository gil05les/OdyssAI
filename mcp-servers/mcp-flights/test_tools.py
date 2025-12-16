#!/usr/bin/env python3
"""
Test script for MCP Flights tools.
Tests each tool individually without the MCP server wrapper.
"""
import os
import sys
import json
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Try to find .env file in project root
    # This file is at: OdyssAI/mcp-servers/mcp-flights/test_tools.py
    # .env is at: OdyssAI/.env
    # So we go up 3 levels: mcp-flights -> mcp-servers -> OdyssAI
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
from tools.autocomplete import autocomplete_airport_or_city
from tools.search import search_flights
from tools.pricing import price_flight_offer
from tools.routes import get_airline_routes
from tools.booking import book_flight


def test_autocomplete():
    """Test autocomplete_airport_or_city tool."""
    print("\n" + "="*80)
    print("Testing: autocomplete_airport_or_city")
    print("="*80)
    
    try:
        result = autocomplete_airport_or_city(
            query="Zurich",
            country_code="CH"
        )
        print("\n✅ Success!")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_flights():
    """Test search_flights tool."""
    print("\n" + "="*80)
    print("Testing: search_flights")
    print("="*80)
    
    # Use dates that are in the future but not too far (typically 30-330 days ahead)
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
    
    print(f"Using dates: {future_date} (departure), {return_date} (return)")
    
    try:
        result = search_flights(
            origin="ZRH",
            destination="LIS",
            departure_date=future_date,
            return_date=return_date,
            adults=1,
            max_price=1000
        )
        print("\n✅ Success!")
        print(f"Found {len(result.get('flight_options', []))} flight options")
        if result.get('flight_options'):
            first_option = result['flight_options'][0]
            print(f"\nFirst option:")
            print(f"  ID: {first_option.get('id')}")
            print(f"  Price: {first_option.get('price')} {first_option.get('currency')}")
            print(f"  Airlines: {', '.join(first_option.get('airlines', []))}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_airline_routes():
    """Test get_airline_routes tool."""
    print("\n" + "="*80)
    print("Testing: get_airline_routes")
    print("="*80)
    
    try:
        result = get_airline_routes(
            airline_code="LX",
            origin="ZRH"
        )
        print("\n✅ Success!")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_price_flight_offer():
    """Test price_flight_offer tool."""
    print("\n" + "="*80)
    print("Testing: price_flight_offer")
    print("="*80)
    
    # First, we need to search for flights to get an offer
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
    
    print(f"Step 1: Searching for flights (departure: {future_date}, return: {return_date})...")
    
    try:
        # Search for flights first
        search_result = search_flights(
            origin="ZRH",
            destination="LIS",
            departure_date=future_date,
            return_date=return_date,
            adults=1
        )
        
        flight_options = search_result.get('flight_options', [])
        if not flight_options:
            print("\n⚠️  No flight options found, cannot test pricing")
            return False
        
        # Get the first offer (we need the original offer data from Amadeus API)
        # Note: The normalized offer from search_flights doesn't have the full structure
        # needed for pricing. In a real scenario, we'd need to store the original offer.
        # For testing, we'll use what we have and see if it works.
        first_offer = flight_options[0]
        offer_id = first_offer.get('id', 'TEST_OFFER')
        
        print(f"Step 2: Pricing offer {offer_id}...")
        print(f"  Note: Using simplified offer data for testing")
        
        # Create a minimal offer structure for pricing
        # In production, you'd use the full original offer from search_flights
        offer_data = {
            'id': offer_id,
            'price': {
                'total': str(first_offer.get('price', 0)),
                'currency': first_offer.get('currency', 'CHF')
            },
            'itineraries': []  # Simplified for testing
        }
        
        result = price_flight_offer(
            offer_id=offer_id,
            offer_data=offer_data
        )
        
        print("\n✅ Success!")
        print(f"Final price: {result.get('final_price')} {result.get('currency')}")
        print(f"Pricing guaranteed: {result.get('pricing_guaranteed', False)}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_book_flight():
    """Test book_flight tool (mocked)."""
    print("\n" + "="*80)
    print("Testing: book_flight (MOCKED)")
    print("="*80)
    
    try:
        # Create mock passenger data
        passengers = [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'dateOfBirth': '1990-01-01',
                'gender': 'MALE',
                'contact': {
                    'emailAddress': 'john.doe@example.com',
                    'phones': [{
                        'deviceType': 'MOBILE',
                        'countryCallingCode': '1',
                        'number': '5551234567'
                    }]
                }
            }
        ]
        
        # Create mock priced offer data
        priced_offer_data = {
            'id': 'MOCK_OFFER_123',
            'price': {
                'total': '420.00',
                'currency': 'CHF'
            }
        }
        
        result = book_flight(
            priced_offer_id='MOCK_OFFER_123',
            priced_offer_data=priced_offer_data,
            passengers=passengers,
            contact_email='john.doe@example.com'
        )
        
        print("\n✅ Success!")
        print(f"Booking ID: {result.get('booking_id')}")
        print(f"PNR: {result.get('pnr')}")
        print(f"Status: {result.get('status')}")
        print(f"Mock: {result.get('mock', False)}")
        print(f"Passengers: {result.get('passengers')}")
        
        # Verify it's a mock booking
        if not result.get('mock', False):
            print("\n⚠️  Warning: This should be a mock booking but 'mock' flag is not set")
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("MCP Flights Tools - Direct Testing")
    print("="*80)
    
    # Check environment variables (support both naming conventions from .env file)
    has_api_key = os.getenv('AMADEUS_API_KEY') or os.getenv('AMADEUS_CLIENT_ID')
    has_api_secret = os.getenv('AMADEUS_API_SECRET') or os.getenv('AMADEUS_CLIENT_SECRET')
    
    if not has_api_key or not has_api_secret:
        print("\n⚠️  Warning: Amadeus credentials not found")
        print("   Please set them in your .env file (project root):")
        print("   AMADEUS_API_KEY=your_key")
        print("   AMADEUS_API_SECRET=your_secret")
        print("   AMADEUS_ENV=prod  # or 'test'")
        print("")
        print("   Or use environment variables:")
        print("   AMADEUS_CLIENT_ID / AMADEUS_API_KEY")
        print("   AMADEUS_CLIENT_SECRET / AMADEUS_API_SECRET")
        return
    
    results = []
    
    # Test autocomplete
    results.append(("autocomplete_airport_or_city", test_autocomplete()))
    
    # Test search flights
    results.append(("search_flights", test_search_flights()))
    
    # Test airline routes
    results.append(("get_airline_routes", test_get_airline_routes()))
    
    # Test pricing (requires successful flight search)
    results.append(("price_flight_offer", test_price_flight_offer()))
    
    # Test booking (mocked, always works)
    results.append(("book_flight (MOCKED)", test_book_flight()))
    
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

