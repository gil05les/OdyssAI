# Date Flow: Frontend → Agent → MCP → Amadeus API

## Overview

This document traces how dates flow through the system from the frontend user input to the Amadeus API call.

## Data Flow

### 1. Frontend (FlightAgent.tsx)

**Source**: User's trip request from the trip planning form
- **Location**: `tripRequest.date_ranges[0]`
- **Format**: `{ from: "2026-01-11", to: "2026-01-18" }` (ISO date strings)

**Processing**:
```typescript
const dateRange = tripRequest.date_ranges[0];
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toISOString().split('T')[0]; // YYYY-MM-DD
};

const departureDate = formatDate(dateRange.from);  // "2026-01-11"
const returnDate = dateRange.to ? formatDate(dateRange.to) : undefined; // "2026-01-18"
```

**Sent to API**:
```typescript
await searchFlights({
  origin: originIata,
  destination: destIata,
  departure_date: departureDate,  // "2026-01-11"
  return_date: returnDate,         // "2026-01-18" or undefined
  adults: tripRequest.group_size,
  max_price: maxPrice,
});
```

### 2. Backend API (api.py)

**Receives**: `FlightInput` model
- **Location**: `/api/flights` endpoint
- **Model**: `FlightInput` with fields:
  - `departure_date: str` (YYYY-MM-DD format)
  - `return_date: Optional[str]` (YYYY-MM-DD format)

**Processing**:
```python
@app.post("/api/flights", response_model=FlightOutput)
async def search_flights(request: FlightInput):
    # request.departure_date = "2026-01-11"
    # request.return_date = "2026-01-18" or None
    
    flight_agent = await get_flight_agent()
    result = await flight_agent.execute(request.model_dump())
    # Passes: {
    #   "departure_date": "2026-01-11",
    #   "return_date": "2026-01-18",
    #   ...
    # }
```

### 3. Flight Agent (flight_agent.py)

**Receives**: Dictionary with dates from API
- **Location**: `execute()` method
- **Format**: `{"departure_date": "2026-01-11", "return_date": "2026-01-18", ...}`

**Processing**:
```python
async def execute(self, params: Dict[str, Any]) -> AgentResult:
    departure_date = params.get("departure_date", "")  # "2026-01-11"
    return_date = params.get("return_date")            # "2026-01-18" or None
    
    flight_output = await self.search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date,  # "2026-01-11"
        return_date=return_date,        # "2026-01-18" or None
        adults=adults,
        max_price=max_price
    )
```

**LLM Prompt**:
```python
prompt = f"""Search for flights from {origin} to {destination}.

Search Parameters:
- Departure Date: {departure_date}  # "2026-01-11"
"""
if return_date:
    prompt += f"- Return Date: {return_date}\n"  # "2026-01-18"
```

**LLM calls MCP tool**: The LLM receives the prompt with dates and calls the `search_flights` MCP tool with these dates.

### 4. MCP Server (mcp-flights/tools/search.py)

**Receives**: Tool call from LLM with dates
- **Location**: `search_flights()` function
- **Parameters**:
  - `departure_date: str` (YYYY-MM-DD format)
  - `return_date: Optional[str]` (YYYY-MM-DD format)

**Processing**:
```python
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,        # "2026-01-11"
    return_date: Optional[str] = None,  # "2026-01-18" or None
    adults: int = 1,
    max_price: Optional[float] = None,
    client: Optional[AmadeusClientWrapper] = None
) -> Dict[str, Any]:
    # Build parameters for Amadeus API
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,  # "2026-01-11"
        'adults': adults
    }
    
    if return_date:
        params['returnDate'] = return_date  # "2026-01-18"
```

### 5. Amadeus API

**Receives**: HTTP GET request to `/v2/shopping/flight-offers`
- **Parameters**:
  - `departureDate`: "2026-01-11" (YYYY-MM-DD)
  - `returnDate`: "2026-01-18" (YYYY-MM-DD, optional)

**API Call**:
```python
response = amadeus.shopping.flight_offers_search.get(**params)
# Calls: GET /v2/shopping/flight-offers?originLocationCode=ZRH&destinationLocationCode=LIS&departureDate=2026-01-11&returnDate=2026-01-18&adults=1
```

## Date Format Throughout

- **Frontend Input**: ISO date strings (`"2026-01-11"`)
- **Frontend → API**: YYYY-MM-DD format (`"2026-01-11"`)
- **API → Agent**: YYYY-MM-DD format (`"2026-01-11"`)
- **Agent → LLM**: YYYY-MM-DD format in prompt (`"2026-01-11"`)
- **LLM → MCP**: YYYY-MM-DD format in tool call (`"2026-01-11"`)
- **MCP → Amadeus**: YYYY-MM-DD format in API params (`"2026-01-11"`)

**All dates are consistently in YYYY-MM-DD format throughout the entire flow.**

## Display in Frontend

The dates are now displayed in the FlightAgent component header:
- **Departure Date**: Formatted as "Jan 11, 2026"
- **Return Date**: Formatted as "Jan 18, 2026" (if provided)

The dates come from `tripRequest.date_ranges[0]` and are formatted for display using `toLocaleDateString()`.

## Verification

✅ **Frontend extracts dates** from `tripRequest.date_ranges[0]`  
✅ **Frontend formats dates** as YYYY-MM-DD for API  
✅ **API receives dates** in `FlightInput` model  
✅ **Agent receives dates** from API  
✅ **Agent includes dates** in LLM prompt  
✅ **LLM calls MCP tool** with dates  
✅ **MCP tool receives dates** and passes to Amadeus API  
✅ **Amadeus API receives dates** in correct format  

**The date flow is correct and working end-to-end!**



