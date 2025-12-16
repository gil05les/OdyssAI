# MCP Servers for Travel Agent

This directory contains Model Context Protocol (MCP) servers for the agentic travel planner. Each server provides specific tools for interacting with travel APIs.

## Overview

The MCP servers are implemented using the standard MCP protocol and are sandboxed using GuardiAgent for secure execution. Each server runs in a Docker container with restricted permissions.

## Available Servers

### mcp-flights

MCP server for flight-related operations using Amadeus APIs.

**Tools:**
1. `autocomplete_airport_or_city` - Convert city/airport names to IATA codes
2. `search_flights` - Search for available flights
3. `price_flight_offer` - Get final pricing for a flight offer
4. `book_flight` - Create a flight booking (PNR)
5. `get_airline_routes` - Get destinations served by an airline

### mcp-hotels

MCP server for hotel-related operations using Amadeus APIs.

**Tools:**
1. `search_hotels_in_city` - Find hotels in a specific city with price and guest filters
2. `search_hotels_by_coordinates` - Find hotels near a specific location using geographic coordinates
3. `get_hotel_offer_details` - Get detailed information about a specific hotel offer (room details, cancellation policy, price breakdown)

### mcp-cars

MCP server for car rental-related operations using Amadeus APIs.

**Tools:**
1. `search_cars_at_airport` - Find rental cars available at a specific airport
2. `get_car_offer_details` - Get detailed information about a specific car rental offer (insurance, cancellation policy, vehicle specifications)

**Note:** The car rental API may require production credentials or a specific Amadeus plan. If you encounter 404 errors, verify that your Amadeus account has access to the car rental endpoints.

### mcp-geo-destinations

MCP server for geographical destination information using RestCountries, OpenWeatherMap, and Amadeus APIs.

**Tools:**
1. `get_country_info` - Get comprehensive country information (currency, languages, timezone, visa notes) from RestCountries API
2. `get_best_travel_season` - Determine optimal travel seasons based on historical weather data from OpenWeatherMap API
3. `get_points_of_interest` - Get points of interest near a location using Amadeus POIs API

## Setup

### Prerequisites

- Python 3.10+
- Docker installed and running
- Amadeus API credentials (client ID and secret)
- OpenAI API key (for the agent)

### Environment Variables

Set the following environment variables in your `.env` file (project root):

**Required for all servers:**
```bash
# Amadeus API (for flights, hotels, cars, POIs)
AMADEUS_API_KEY="your_amadeus_api_key"          # or AMADEUS_CLIENT_ID
AMADEUS_API_SECRET="your_amadeus_api_secret"    # or AMADEUS_CLIENT_SECRET
AMADEUS_ENV="test"                              # or "prod" for production
```

**Required for mcp-geo-destinations:**
```bash
# OpenWeatherMap API (for get_best_travel_season)
OPENWEATHERMAP_API_KEY="your_openweathermap_api_key"
```

**Optional:**
```bash
# OpenAI API (for the agent)
OPENAI_API_KEY="your_openai_key"
```

**Getting API Keys:**
- **Amadeus**: Sign up at https://developers.amadeus.com/ (free test account available)
- **OpenWeatherMap**: Sign up at https://openweathermap.org/api (free tier available with 1,000 calls/day)
- **RestCountries**: No API key required (free public API)

### Installation

1. Install dependencies for the MCP servers:

```bash
# For mcp-flights
cd mcp-servers/mcp-flights
pip install -r requirements.txt

# For mcp-hotels
cd ../mcp-hotels
pip install -r requirements.txt

# For mcp-cars
cd ../mcp-cars
pip install -r requirements.txt

# For mcp-geo-destinations
cd ../mcp-geo-destinations
pip install -r requirements.txt
```

2. Install the MCP sandbox SDK (if not already installed):

```bash
cd ../../python-mcp-sandbox-openai-sdk-main
pip install -e .
```

3. Install backend dependencies:

```bash
cd ../../backend
pip install openai-agents
```

## Running the Server

### Using the Backend Application

Run the main application which will start the MCP server in a sandbox:

```bash
cd backend
python main.py
```

The application will:
1. Mount the mcp-flights server code into a Docker container
2. Request user consent for network and environment variable access
3. Start the agent with the MCP server
4. Execute a test query

### Direct Server Testing

To test the MCP server directly (without sandboxing):

```bash
cd mcp-servers/mcp-flights
python server.py
```

The server communicates via JSON-RPC over stdin/stdout.

## Tool Usage Examples

### autocomplete_airport_or_city

```json
{
  "name": "autocomplete_airport_or_city",
  "arguments": {
    "query": "Zurich",
    "country_code": "CH"
  }
}
```

**Response:**
```json
{
  "locations": [
    {
      "iata": "ZRH",
      "type": "AIRPORT",
      "city": "Zurich",
      "country": "CH"
    }
  ]
}
```

### search_flights

```json
{
  "name": "search_flights",
  "arguments": {
    "origin": "ZRH",
    "destination": "LIS",
    "departure_date": "2025-05-10",
    "return_date": "2025-05-17",
    "adults": 1,
    "max_price": 1000
  }
}
```

**Response:**
```json
{
  "flight_options": [
    {
      "id": "OFFER_123",
      "price": 420,
      "currency": "CHF",
      "segments": [...],
      "airlines": ["LX", "TP"]
    }
  ]
}
```

### price_flight_offer

```json
{
  "name": "price_flight_offer",
  "arguments": {
    "offer_id": "OFFER_123",
    "offer_data": {...}  // Full offer object from search_flights
  }
}
```

### book_flight

```json
{
  "name": "book_flight",
  "arguments": {
    "priced_offer_id": "OFFER_123",
    "priced_offer_data": {...},  // Full priced offer from price_flight_offer
    "passengers": [
      {
        "firstName": "John",
        "lastName": "Doe",
        "dateOfBirth": "1990-01-01",
        "gender": "MALE",
        "contact": {
          "emailAddress": "john.doe@example.com",
          "phones": [{"deviceType": "MOBILE", "countryCallingCode": "1", "number": "5551234567"}]
        }
      }
    ],
    "contact_email": "user@mail.com"
  }
}
```

### get_airline_routes

```json
{
  "name": "get_airline_routes",
  "arguments": {
    "airline_code": "LX",
    "origin": "ZRH"
  }
}
```

## mcp-hotels Tool Usage Examples

### search_hotels_in_city

```json
{
  "name": "search_hotels_in_city",
  "arguments": {
    "city_code": "LIS",
    "check_in": "2025-05-10",
    "check_out": "2025-05-17",
    "guests": 2,
    "max_price_per_night": 150
  }
}
```

**Response:**
```json
{
  "hotel_offers": [
    {
      "offer_id": "NZK1U4GUZZ",
      "hotel_id": "HOLISAGD",
      "hotel_name": "HOLIDAY INN LISBON-CONTINENTAL",
      "price_total": 748.58,
      "price_per_night": 106.94,
      "currency": "EUR",
      "room_type": "STANDARD_ROOM",
      "check_in": "2025-05-10",
      "check_out": "2025-05-17",
      "guests": 2,
      "nights": 7
    }
  ],
  "total_offers": 1,
  "city_code": "LIS"
}
```

### search_hotels_by_coordinates

```json
{
  "name": "search_hotels_by_coordinates",
  "arguments": {
    "latitude": 38.7223,
    "longitude": -9.1393,
    "radius": 5.0,
    "radius_unit": "KM",
    "check_in": "2025-05-10",
    "check_out": "2025-05-17",
    "guests": 2
  }
}
```

**Response:**
```json
{
  "hotels": [
    {
      "hotel_id": "HSLISACX",
      "name": "LISBON CITY",
      "geo_code": {
        "latitude": 38.7223,
        "longitude": -9.1393
      },
      "distance": 0.5,
      "distance_unit": "KM"
    }
  ],
  "total_hotels": 15,
  "coordinates": {
    "latitude": 38.7223,
    "longitude": -9.1393
  }
}
```

### get_hotel_offer_details

```json
{
  "name": "get_hotel_offer_details",
  "arguments": {
    "offer_id": "NZK1U4GUZZ"
  }
}
```

**Response:**
```json
{
  "offer_details": {
    "offer_id": "NZK1U4GUZZ",
    "hotel": {
      "hotel_id": "HOLISAGD",
      "name": "HOLIDAY INN LISBON-CONTINENTAL",
      "rating": "4",
      "amenities": ["WiFi", "Parking", "Pool"]
    },
    "room": {
      "type": "STANDARD_ROOM",
      "beds": 1,
      "bed_type": "DOUBLE",
      "description": "Standard room with city view"
    },
    "price": {
      "total": 748.58,
      "currency": "EUR",
      "base": 600.00,
      "taxes": [...]
    },
    "cancellation_policy": {
      "type": "FREE_CANCELLATION",
      "deadline": "2025-05-09T18:00:00"
    }
  }
}
```

## mcp-cars Tool Usage Examples

### search_cars_at_airport

```json
{
  "name": "search_cars_at_airport",
  "arguments": {
    "pickup_iata": "LIS",
    "pickup_date": "2025-05-10",
    "dropoff_date": "2025-05-17",
    "pickup_time": "10:00",
    "dropoff_time": "10:00"
  }
}
```

**Response:**
```json
{
  "car_offers": [
    {
      "offer_id": "CAR_OFFER_123",
      "provider": "Hertz",
      "vehicle": {
        "category": "ECONOMY",
        "make": "Ford",
        "model": "Fiesta",
        "transmission": "MANUAL",
        "air_conditioning": true,
        "fuel": "PETROL",
        "seats": 5,
        "doors": 4
      },
      "pricing": {
        "total": 350.00,
        "currency": "EUR",
        "base": 280.00,
        "taxes": [...]
      },
      "pickup_location": {
        "code": "LIS",
        "name": "Lisbon Airport"
      }
    }
  ],
  "total_offers": 10,
  "pickup_iata": "LIS"
}
```

### get_car_offer_details

```json
{
  "name": "get_car_offer_details",
  "arguments": {
    "offer_id": "CAR_OFFER_123"
  }
}
```

**Response:**
```json
{
  "offer_details": {
    "offer_id": "CAR_OFFER_123",
    "provider": {
      "name": "Hertz",
      "code": "ZT"
    },
    "vehicle": {
      "category": "ECONOMY",
      "make": "Ford",
      "model": "Fiesta",
      "transmission": "MANUAL",
      "seats": 5,
      "doors": 4
    },
    "pricing": {
      "total": 350.00,
      "currency": "EUR",
      "base": 280.00,
      "taxes": [...],
      "fees": [...]
    },
    "insurance": [
      {
        "type": "CDW",
        "included": true,
        "coverage": {...},
        "description": "Collision Damage Waiver"
      }
    ],
    "cancellation_policy": {
      "type": "FREE_CANCELLATION",
      "deadline": "2025-05-09T18:00:00",
      "description": "Free cancellation until 24 hours before pickup"
    },
    "terms": {
      "mileage": {...},
      "age_requirements": {...},
      "driver_requirements": [...]
    }
  }
}
```

## mcp-geo-destinations Tool Usage Examples

### get_country_info

```json
{
  "name": "get_country_info",
  "arguments": {
    "country_code": "CH"
  }
}
```

**Response:**
```json
{
  "country": "Switzerland",
  "country_official": "Swiss Confederation",
  "country_code_alpha2": "CH",
  "country_code_alpha3": "CHE",
  "currency": {
    "code": "CHF",
    "name": "Swiss franc",
    "symbol": "Fr."
  },
  "languages": ["German", "French", "Italian", "Romansh"],
  "timezone": "UTC+01:00",
  "timezones": ["UTC+01:00"],
  "capital": "Bern",
  "region": "Europe",
  "subregion": "Western Europe",
  "population": 8654622,
  "visa_info": {
    "note": "Visa requirements vary by nationality. Check with embassy for specific requirements."
  }
}
```

### get_best_travel_season

```json
{
  "name": "get_best_travel_season",
  "arguments": {
    "latitude": 38.7223,
    "longitude": -9.1393,
    "city_name": "Lisbon",
    "country_code": "PT"
  }
}
```

**Response:**
```json
{
  "destination": {
    "city": "Lisbon",
    "country_code": "PT",
    "coordinates": {
      "latitude": 38.7223,
      "longitude": -9.1393
    }
  },
  "best_months": ["May", "June", "September", "October"],
  "best_months_detailed": [
    {
      "month": "May",
      "score": 18,
      "temperature": {
        "min": 15.2,
        "max": 22.5,
        "average": 18.8
      },
      "precipitation": {
        "total_mm": 45.3,
        "probability": 0.15
      }
    }
  ],
  "weather_by_month": {
    "January": {...},
    "February": {...}
  },
  "recommendations": [
    "Best time to visit: May, June, September, October",
    "Spring average temperature: 18.5°C",
    "Summer average temperature: 23.2°C"
  ]
}
```

### get_points_of_interest

```json
{
  "name": "get_points_of_interest",
  "arguments": {
    "latitude": 38.7223,
    "longitude": -9.1393,
    "radius": 5.0,
    "radius_unit": "KM"
  }
}
```

**Response:**
```json
{
  "pois": [
    {
      "poi_id": "POI_123",
      "name": "Belém Tower",
      "category": "SIGHTSEEING",
      "subcategory": "MONUMENT",
      "geo_code": {
        "latitude": 38.6916,
        "longitude": -9.2160
      },
      "address": {
        "city_name": "Lisbon",
        "country_code": "PT"
      },
      "distance": 2.5,
      "distance_unit": "KM"
    }
  ],
  "total_pois": 15,
  "by_category": {
    "SIGHTSEEING": [...],
    "RESTAURANT": [...]
  }
}
```

## Logging

All MCP servers implement comprehensive logging:

- **Tool Entry**: Logs tool name and input parameters (sensitive data sanitized)
- **API Calls**: Logs Amadeus API endpoint and request parameters
- **API Responses**: Logs response status and data size
- **Errors**: Logs full error details with stack traces
- **Performance**: Logs execution time for each tool call

Log format: `[TIMESTAMP] [LEVEL] [TOOL] [REQ:REQUEST_ID] MESSAGE`

Logs are written to stdout (for MCP stdio compatibility) and can optionally be written to files.

## Architecture

### Server Structure

```
mcp-flights/
├── server.py              # Main MCP server (JSON-RPC over stdio)
├── tools/                 # Tool implementations
│   ├── autocomplete.py
│   ├── search.py
│   ├── pricing.py
│   ├── booking.py
│   └── routes.py
├── amadeus_client.py      # Amadeus API client wrapper
├── logger.py              # Logging configuration
├── requirements.txt       # Python dependencies
└── manifest.json          # MCP manifest (for reference)

mcp-hotels/
├── server.py              # Main MCP server (JSON-RPC over stdio)
├── tools/                 # Tool implementations
│   ├── search_city.py
│   ├── search_coordinates.py
│   └── offer_details.py
├── amadeus_client.py      # Amadeus API client wrapper
├── logger.py              # Logging configuration
├── requirements.txt       # Python dependencies
└── manifest.json          # MCP manifest (for reference)

mcp-cars/
├── server.py              # Main MCP server (JSON-RPC over stdio)
├── tools/                 # Tool implementations
│   ├── search_airport.py
│   └── offer_details.py
├── amadeus_client.py      # Amadeus API client wrapper
├── logger.py              # Logging configuration
├── requirements.txt       # Python dependencies
└── manifest.json          # MCP manifest (for reference)

mcp-geo-destinations/
├── server.py              # Main MCP server (JSON-RPC over stdio)
├── tools/                 # Tool implementations
│   ├── country_info.py    # RestCountries API
│   ├── travel_season.py   # OpenWeatherMap API
│   └── points_of_interest.py  # Amadeus POIs API
├── logger.py              # Logging configuration
├── requirements.txt       # Python dependencies
└── manifest.json          # MCP manifest (for reference)
```

### Communication Flow

1. Agent sends JSON-RPC request via stdin
2. MCP server parses request and routes to appropriate tool
3. Tool calls Amadeus API via client wrapper
4. Response is normalized and returned as JSON-RPC response via stdout

### Sandboxing

The server runs in a Docker container with:
- Network access restricted to Amadeus API domain
- Environment variable access for API credentials
- No filesystem write access (unless explicitly granted)

## Development

### Adding New Tools

1. Create a new tool file in `tools/` directory
2. Implement the tool function with proper logging
3. Register the tool in `server.py` with schema
4. Update this README with usage examples

### Testing

Test individual tools:

```python
from tools.search import search_flights
from amadeus_client import AmadeusClientWrapper

client = AmadeusClientWrapper()
result = search_flights(
    origin="ZRH",
    destination="LIS",
    departure_date="2025-05-10",
    client=client
)
print(result)
```

## Troubleshooting

### Server Not Starting

- Check Docker is running: `docker ps`
- Verify environment variables are set
- Check logs for permission errors

### API Errors

- Verify Amadeus credentials are correct
- Check API rate limits
- Ensure you're using the correct environment (test vs production)

### Tool Execution Errors

- Check tool input parameters match schema
- Verify Amadeus API endpoint is accessible
- Review logs for detailed error messages

## Future Servers

Additional MCP servers planned:
- `mcp-user-data` - User data management (Supabase)

