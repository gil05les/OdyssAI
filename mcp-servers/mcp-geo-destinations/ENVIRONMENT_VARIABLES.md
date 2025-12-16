# Environment Variables for mcp-geo-destinations

## Required Environment Variables

Add these to your `.env` file in the project root:

### 1. OpenWeatherMap API Key (Required for `get_best_travel_season`)

```bash
OPENWEATHERMAP_API_KEY="your_openweathermap_api_key_here"
```

**How to get it:**
1. Sign up for a free account at https://openweathermap.org/api
2. Navigate to your API keys section
3. Copy your API key
4. Free tier includes 1,000 calls/day and 60 calls/minute

**API Endpoint Used:**
- One Call API 3.0 - Day Summary: `https://api.openweathermap.org/data/3.0/onecall/day_summary`
- Provides historical weather data for analyzing best travel seasons

### 2. Amadeus API Credentials (Required for `get_points_of_interest`)

```bash
AMADEUS_API_KEY="your_amadeus_api_key"          # or use AMADEUS_CLIENT_ID
AMADEUS_API_SECRET="your_amadeus_api_secret"    # or use AMADEUS_CLIENT_SECRET
AMADEUS_ENV="test"                              # or "prod" for production
```

**How to get it:**
1. Sign up at https://developers.amadeus.com/
2. Create a new app in the developer portal
3. Copy your API Key and API Secret
4. Free test account available

**Note:** The code supports both naming conventions:
- `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` (preferred)
- `AMADEUS_CLIENT_ID` / `AMADEUS_CLIENT_SECRET` (alternative)

### 3. RestCountries API (No API key required)

The `get_country_info` tool uses RestCountries API which is free and doesn't require authentication.

**API Endpoint:**
- RestCountries v3.1: `https://restcountries.com/v3.1/`

## Example .env File

```bash
# OpenWeatherMap API (for get_best_travel_season)
OPENWEATHERMAP_API_KEY=abc123def456ghi789jkl012mno345pqr678

# Amadeus API (for get_points_of_interest, also used by other MCP servers)
AMADEUS_API_KEY=your_amadeus_api_key_here
AMADEUS_API_SECRET=your_amadeus_api_secret_here
AMADEUS_ENV=test

# Optional: OpenAI API (for the agent)
OPENAI_API_KEY=your_openai_key_here
```

## Testing

After setting up your environment variables, test the tools:

```bash
cd mcp-servers/mcp-geo-destinations
python3 test_tools.py
```

This will test all three tools and show which ones require API keys.






