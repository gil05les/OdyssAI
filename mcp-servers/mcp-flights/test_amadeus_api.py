#!/usr/bin/env python3
"""
Simple test script for Amadeus Flight API.
Makes a single API call to verify connectivity and authentication.
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
    # This file is at: OdyssAI/mcp-servers/mcp-flights/test_amadeus_api.py
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


def test_amadeus_api():
    """Test Amadeus API with a simple flight search."""
    print("\n" + "="*80)
    print("Testing Amadeus Flight API")
    print("="*80)
    
    # Check credentials
    has_api_key = os.getenv('AMADEUS_API_KEY') or os.getenv('AMADEUS_CLIENT_ID')
    has_api_secret = os.getenv('AMADEUS_API_SECRET') or os.getenv('AMADEUS_CLIENT_SECRET')
    
    if not has_api_key or not has_api_secret:
        print("\n❌ Error: Amadeus credentials not found")
        print("   Please set them in your .env file (project root):")
        print("   AMADEUS_API_KEY=your_key")
        print("   AMADEUS_API_SECRET=your_secret")
        print("   AMADEUS_ENV=test  # or 'prod'")
        return False
    
    try:
        # Initialize client
        print("\n📡 Initializing Amadeus client...")
        client = AmadeusClientWrapper()
        amadeus = client.get_client()
        print("✅ Client initialized successfully")
        
        # Prepare test parameters
        # Use dates that are in the future (typically 30-330 days ahead for Amadeus)
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        params = {
            'originLocationCode': 'ZRH',  # Zurich
            'destinationLocationCode': 'LIS',  # Lisbon
            'departureDate': future_date,
            'adults': 1
        }
        
        print(f"\n🔍 Making API call: Flight Offers Search")
        print(f"   Origin: {params['originLocationCode']}")
        print(f"   Destination: {params['destinationLocationCode']}")
        print(f"   Departure Date: {params['departureDate']}")
        print(f"   Adults: {params['adults']}")
        
        # Make API call
        response = amadeus.shopping.flight_offers_search.get(**params)
        
        # Check response
        if response.data:
            print(f"\n✅ Success! Received {len(response.data)} flight offers")
            
            # Display first offer summary
            if len(response.data) > 0:
                first_offer = response.data[0]
                price_info = first_offer.get('price', {})
                print(f"\n📋 First Offer Summary:")
                print(f"   ID: {first_offer.get('id', 'N/A')}")
                print(f"   Price: {price_info.get('total', 'N/A')} {price_info.get('currency', 'N/A')}")
                print(f"   Bookable Seats: {first_offer.get('numberOfBookableSeats', 'N/A')}")
                
                # Show segments
                itineraries = first_offer.get('itineraries', [])
                if itineraries:
                    print(f"   Segments: {len(itineraries)} itinerary(ies)")
                    for idx, itinerary in enumerate(itineraries, 1):
                        segments = itinerary.get('segments', [])
                        print(f"      Itinerary {idx}: {len(segments)} segment(s)")
                        for seg_idx, segment in enumerate(segments, 1):
                            dep = segment.get('departure', {})
                            arr = segment.get('arrival', {})
                            print(f"         Segment {seg_idx}: {dep.get('iataCode', 'N/A')} -> {arr.get('iataCode', 'N/A')}")
                            print(f"            {dep.get('at', 'N/A')} -> {arr.get('at', 'N/A')}")
            
            # Optionally show full response (truncated)
            print(f"\n📄 Response preview (first 500 chars):")
            response_str = json.dumps(response.data[0] if response.data else {}, indent=2)
            print(response_str[:500] + ("..." if len(response_str) > 500 else ""))
            
            return True
        else:
            print("\n⚠️  API call succeeded but no flight offers returned")
            print("   This might be normal if no flights are available for the given route/date")
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        error_type = type(e).__name__
        print(f"   Error type: {error_type}")
        
        # Try to get more details
        if hasattr(e, 'description'):
            try:
                desc = e.description() if callable(e.description) else str(e.description)
                print(f"   Description: {desc}")
            except:
                pass
        
        if hasattr(e, 'code'):
            print(f"   Error code: {e.code}")
        
        if hasattr(e, 'response'):
            print(f"   Response: {e.response}")
        
        import traceback
        print(f"\n📋 Full traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_amadeus_api()
    
    print("\n" + "="*80)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
    print("="*80)
    
    sys.exit(0 if success else 1)



