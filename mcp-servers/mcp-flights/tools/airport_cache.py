"""
Airport caching module for MCP Flights.
Provides local airport database lookup and API response caching.
"""
import json
import time
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class AirportDatabase:
    """
    Local database of major airports for instant lookups.
    Loads from airports.json and provides fuzzy search.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the airport database.
        
        Args:
            data_path: Path to airports.json (auto-detected if not provided)
        """
        self._airports: List[Dict[str, Any]] = []
        self._loaded = False
        
        # Auto-detect data path
        if data_path is None:
            # This file is at: mcp-flights/tools/airport_cache.py
            # Data is at: mcp-flights/data/airports.json
            current_dir = Path(__file__).parent.parent
            data_path = current_dir / "data" / "airports.json"
        
        self._data_path = Path(data_path)
        self._load_data()
    
    def _load_data(self):
        """Load airport data from JSON file."""
        if self._loaded:
            return
        
        try:
            if self._data_path.exists():
                with open(self._data_path, 'r', encoding='utf-8') as f:
                    self._airports = json.load(f)
                self._loaded = True
        except Exception as e:
            # Silently fail - will just use API fallback
            self._airports = []
            self._loaded = True
    
    def search(self, query: str, country_code: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for airports matching the query.
        
        Args:
            query: Search query (city name, airport name, or IATA code)
            country_code: Optional ISO country code filter
            limit: Maximum results to return
        
        Returns:
            List of matching airports in normalized format
        """
        if not self._airports:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        for airport in self._airports:
            # Skip if country code filter doesn't match
            if country_code and airport.get('country', '').upper() != country_code.upper():
                continue
            
            # Check for exact IATA match (highest priority)
            if airport.get('iata', '').lower() == query_lower:
                results.insert(0, airport)  # Insert at front for exact matches
                continue
            
            # Check city name
            if query_lower in airport.get('city', '').lower():
                results.append(airport)
                continue
            
            # Check airport name
            if query_lower in airport.get('name', '').lower():
                results.append(airport)
                continue
            
            # Check keywords
            keywords = airport.get('keywords', [])
            if any(query_lower in kw.lower() for kw in keywords):
                results.append(airport)
                continue
        
        # Convert to normalized format and limit results
        normalized = []
        for airport in results[:limit]:
            normalized.append({
                'iata': airport.get('iata', ''),
                'type': 'AIRPORT',
                'city': airport.get('city', ''),
                'country': airport.get('country', ''),
                'name': airport.get('name', '')
            })
        
        return normalized
    
    @property
    def airport_count(self) -> int:
        """Return the number of airports in the database."""
        return len(self._airports)


class APICache:
    """
    TTL-based cache for API responses.
    Stores results in memory with configurable expiration.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize the API cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self._cache: Dict[str, tuple] = {}  # key -> (result, timestamp)
        self._ttl = ttl_seconds
    
    def _make_key(self, query: str, country_code: Optional[str] = None) -> str:
        """Generate cache key from query parameters."""
        return f"{query.lower().strip()}|{(country_code or '').upper()}"
    
    def get(self, query: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result if available and not expired.
        
        Args:
            query: Search query
            country_code: Optional country code filter
        
        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(query, country_code)
        
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return result
            # Expired - remove from cache
            del self._cache[key]
        
        return None
    
    def set(self, query: str, country_code: Optional[str], result: Dict[str, Any]):
        """
        Store result in cache.
        
        Args:
            query: Search query
            country_code: Optional country code filter
            result: Result to cache
        """
        key = self._make_key(query, country_code)
        self._cache[key] = (result, time.time())
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
    
    def clear_expired(self):
        """Remove expired entries from cache."""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if now - timestamp >= self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    @property
    def size(self) -> int:
        """Return the number of entries in the cache."""
        return len(self._cache)


class FlightSearchCache(APICache):
    """
    Cache for flight search results.
    Uses shorter TTL (15 minutes) since prices change frequently.
    """
    
    def __init__(self):
        """Initialize flight search cache with 15-minute TTL."""
        super().__init__(ttl_seconds=900)  # 15 minutes
    
    def _make_key(self, origin: str, destination: str, departure_date: str, 
                  return_date: Optional[str] = None, adults: int = 1) -> str:
        """Generate cache key from flight search parameters."""
        return f"{origin.upper()}|{destination.upper()}|{departure_date}|{return_date or ''}|{adults}"
    
    def get(self, origin: str, destination: str, departure_date: str,
            return_date: Optional[str] = None, adults: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get cached flight search result if available and not expired.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            adults: Number of adult passengers
        
        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(origin, destination, departure_date, return_date, adults)
        
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return result
            # Expired - remove from cache
            del self._cache[key]
        
        return None
    
    def set(self, origin: str, destination: str, departure_date: str,
            return_date: Optional[str], adults: int, result: Dict[str, Any]):
        """
        Store flight search result in cache.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            adults: Number of adult passengers
            result: Result to cache
        """
        key = self._make_key(origin, destination, departure_date, return_date, adults)
        self._cache[key] = (result, time.time())


class RoutesCache(APICache):
    """
    Cache for airline routes.
    Uses longer TTL (24 hours) since routes rarely change.
    """
    
    def __init__(self):
        """Initialize routes cache with 24-hour TTL."""
        super().__init__(ttl_seconds=86400)  # 24 hours
    
    def _make_key(self, airline_code: str, origin: Optional[str] = None) -> str:
        """Generate cache key from airline routes parameters."""
        return f"{airline_code.upper()}|{origin.upper() if origin else ''}"
    
    def get(self, airline_code: str, origin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached airline routes result if available and not expired.
        
        Args:
            airline_code: IATA airline code
            origin: Optional origin airport code
        
        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(airline_code, origin)
        
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return result
            # Expired - remove from cache
            del self._cache[key]
        
        return None
    
    def set(self, airline_code: str, origin: Optional[str], result: Dict[str, Any]):
        """
        Store airline routes result in cache.
        
        Args:
            airline_code: IATA airline code
            origin: Optional origin airport code
            result: Result to cache
        """
        key = self._make_key(airline_code, origin)
        self._cache[key] = (result, time.time())


# Global instances for use across the module
_airport_db: Optional[AirportDatabase] = None
_api_cache: Optional[APICache] = None
_flight_search_cache: Optional[FlightSearchCache] = None
_routes_cache: Optional[RoutesCache] = None


def get_airport_database() -> AirportDatabase:
    """Get the global airport database instance."""
    global _airport_db
    if _airport_db is None:
        _airport_db = AirportDatabase()
    return _airport_db


def get_api_cache() -> APICache:
    """Get the global API cache instance."""
    global _api_cache
    if _api_cache is None:
        _api_cache = APICache(ttl_seconds=3600)  # 1 hour TTL
    return _api_cache


def get_flight_search_cache() -> FlightSearchCache:
    """Get the global flight search cache instance."""
    global _flight_search_cache
    if _flight_search_cache is None:
        _flight_search_cache = FlightSearchCache()
    return _flight_search_cache


def get_routes_cache() -> RoutesCache:
    """Get the global routes cache instance."""
    global _routes_cache
    if _routes_cache is None:
        _routes_cache = RoutesCache()
    return _routes_cache

