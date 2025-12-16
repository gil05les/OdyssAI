"""
Orchestrator Agent

Main coordinator that manages the workflow between specialized agents.
Parses user queries, determines which agents to invoke, and aggregates results.

All agents use GuardiAgent MCP Sandbox (via mcp_sandbox_openai_sdk) to securely
run MCP servers in Docker containers with restricted permissions.
"""

import os
import sys
from typing import Optional, Dict, Any, List
import re

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(backend_dir, '..', 'python-mcp-sandbox-openai-sdk-main', 'src'))
sys.path.insert(0, backend_dir)

# Import from openai-agents package (no naming conflict now that local directory is renamed)
from agents import Agent, Runner
from mcp_sandbox_openai_sdk import (
    DevMCPManifest,
    MCPServers,
    Permission,
    Registry,
    SandboxedMCPStdio,
)

from config import Config
from .destination_agent import DestinationAgent
from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent
from .transport_agent import TransportAgent
from models import TripRequest, Destination


class Orchestrator:
    """
    Orchestrator that coordinates multiple specialized agents.
    
    Manages workflow:
    1. Parse user query
    2. Determine required agents
    3. Invoke destination agent (if needed)
    4. Invoke flight agent (if needed)
    5. Invoke hotel agent (if needed)
    6. Invoke transport agent (if needed)
    7. Aggregate and return results
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            model: Model to use for orchestrator and agents (defaults to Config.DEFAULT_MODEL)
        """
        self.model = model or Config.DEFAULT_MODEL
        self.destination_agent: Optional[DestinationAgent] = None
        self.flight_agent: Optional[FlightAgent] = None
        self.hotel_agent: Optional[HotelAgent] = None
        self.transport_agent: Optional[TransportAgent] = None
    
    async def _get_destination_agent(self) -> DestinationAgent:
        """Get or create destination agent."""
        if self.destination_agent is None:
            self.destination_agent = DestinationAgent(model=self.model)
        return self.destination_agent
    
    async def _get_flight_agent(self) -> FlightAgent:
        """Get or create flight agent."""
        if self.flight_agent is None:
            self.flight_agent = FlightAgent(model=self.model)
        return self.flight_agent
    
    async def _get_hotel_agent(self) -> HotelAgent:
        """Get or create hotel agent."""
        if self.hotel_agent is None:
            self.hotel_agent = HotelAgent(model=self.model)
        return self.hotel_agent
    
    async def _get_transport_agent(self) -> TransportAgent:
        """Get or create transport agent."""
        if self.transport_agent is None:
            self.transport_agent = TransportAgent(model=self.model)
        return self.transport_agent
    
    def _needs_destination_search(self, query: str) -> bool:
        """
        Determine if the query needs destination discovery.
        
        Args:
            query: User query
        
        Returns:
            True if destination search is needed
        """
        # Check for vague destination requests
        vague_patterns = [
            r'\b(beach|beaches)\b',
            r'\b(mountain|mountains|alpine)\b',
            r'\b(cultural|culture)\b',
            r'\b(nightlife|night life)\b',
            r'\b(adventure|adventurous)\b',
            r'\b(relaxing|relax)\b',
            r'\b(romantic|romance)\b',
            r'\b(family|families)\b',
            r'\b(budget|cheap|affordable)\b',
            r'\b(luxury|luxurious)\b',
            r'\b(suggest|recommend|find me|where should|what.*destination)\b',
        ]
        
        query_lower = query.lower()
        for pattern in vague_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check if query mentions specific cities/airports
        # If it does, might not need destination search
        iata_pattern = r'\b[A-Z]{3}\b'  # IATA codes are 3 uppercase letters
        has_iata = bool(re.search(iata_pattern, query))
        
        # If no specific destinations mentioned, might need search
        city_keywords = ['city', 'cities', 'destination', 'destinations', 'place', 'places']
        has_city_keywords = any(keyword in query_lower for keyword in city_keywords)
        
        return has_city_keywords and not has_iata
    
    def _needs_flight_search(self, query: str) -> bool:
        """
        Determine if the query needs flight search.
        
        Args:
            query: User query
        
        Returns:
            True if flight search is needed
        """
        flight_keywords = [
            'flight', 'flights', 'fly', 'flying', 'airline', 'airlines',
            'book', 'booking', 'ticket', 'tickets', 'departure', 'arrival',
            'airport', 'airports'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in flight_keywords)
    
    def _needs_hotel_search(self, query: str) -> bool:
        """
        Determine if the query needs hotel search.
        
        Args:
            query: User query
        
        Returns:
            True if hotel search is needed
        """
        hotel_keywords = [
            'hotel', 'hotels', 'accommodation', 'accommodations', 'lodging',
            'stay', 'staying', 'room', 'rooms', 'check-in', 'check-out',
            'check in', 'check out', 'reservation', 'reservations'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in hotel_keywords)
    
    def _needs_transport_search(self, query: str) -> bool:
        """
        Determine if the query needs transport/car rental search.
        
        Args:
            query: User query
        
        Returns:
            True if transport search is needed
        """
        transport_keywords = [
            'car', 'cars', 'rental', 'rent a car', 'vehicle', 'vehicles',
            'transport', 'transportation', 'pickup', 'dropoff', 'drop-off',
            'pick-up', 'drive', 'driving', 'rental car'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in transport_keywords)
    
    def _extract_flight_info(self, query: str) -> Dict[str, Any]:
        """
        Extract flight information from query.
        
        Args:
            query: User query
        
        Returns:
            Dictionary with extracted flight information
        """
        info = {
            'origin': None,
            'destination': None,
            'departure_date': None,
            'return_date': None,
            'adults': 1,
        }
        
        # Extract dates (YYYY-MM-DD format)
        date_pattern = r'\b(\d{4}-\d{2}-\d{2})\b'
        dates = re.findall(date_pattern, query)
        if dates:
            info['departure_date'] = dates[0]
            if len(dates) > 1:
                info['return_date'] = dates[1]
        
        # Extract IATA codes (3 uppercase letters)
        iata_pattern = r'\b([A-Z]{3})\b'
        iata_codes = re.findall(iata_pattern, query)
        if len(iata_codes) >= 2:
            info['origin'] = iata_codes[0]
            info['destination'] = iata_codes[1]
        elif len(iata_codes) == 1:
            info['destination'] = iata_codes[0]
        
        # Extract number of passengers
        passenger_patterns = [
            r'(\d+)\s*(?:adult|adults|passenger|passengers|person|people)',
            r'for\s+(\d+)',
        ]
        for pattern in passenger_patterns:
            match = re.search(pattern, query.lower())
            if match:
                info['adults'] = int(match.group(1))
                break
        
        return info
    
    async def orchestrate(self, user_query: str) -> str:
        """
        Main orchestration method.
        
        Args:
            user_query: User's travel query
        
        Returns:
            Consolidated response from all agents
        """
        results = []
        
        # Determine which agents are needed
        needs_destination = self._needs_destination_search(user_query)
        needs_flight = self._needs_flight_search(user_query)
        needs_hotel = self._needs_hotel_search(user_query)
        needs_transport = self._needs_transport_search(user_query)
        
        print(f"Orchestrator Analysis:")
        print(f"  - Needs destination search: {needs_destination}")
        print(f"  - Needs flight search: {needs_flight}")
        print(f"  - Needs hotel search: {needs_hotel}")
        print(f"  - Needs transport search: {needs_transport}")
        print()
        
        # Step 1: Destination discovery (if needed)
        if needs_destination:
            print("Invoking Destination Agent...")
            destination_agent = await self._get_destination_agent()
            try:
                destination_result = await destination_agent.discover_destinations(user_query)
                results.append({
                    'agent': 'Destination Search',
                    'result': destination_result
                })
                print("Destination Agent completed.")
                print()
            except Exception as e:
                print(f"Error in destination agent: {e}")
                results.append({
                    'agent': 'Destination Search',
                    'result': f"Error: {str(e)}"
                })
        
        # Step 2: Flight search (if needed)
        if needs_flight:
            print("Invoking Flight Agent...")
            flight_agent = await self._get_flight_agent()
            try:
                # Extract flight information
                flight_info = self._extract_flight_info(user_query)
                
                if flight_info.get('origin') and flight_info.get('destination') and flight_info.get('departure_date'):
                    # Use structured flight search
                    flight_result = await flight_agent.search_flights(
                        origin=flight_info['origin'],
                        destination=flight_info['destination'],
                        departure_date=flight_info['departure_date'],
                        return_date=flight_info.get('return_date'),
                        adults=flight_info.get('adults', 1)
                    )
                else:
                    # Use general query handler
                    flight_result = await flight_agent.handle_flight_query(user_query)
                
                results.append({
                    'agent': 'Flight',
                    'result': flight_result
                })
                print("Flight Agent completed.")
                print()
            except Exception as e:
                print(f"Error in flight agent: {e}")
                results.append({
                    'agent': 'Flight',
                    'result': f"Error: {str(e)}"
                })
        
        # Step 3: Hotel search (if needed)
        if needs_hotel:
            print("Invoking Hotel Agent...")
            hotel_agent = await self._get_hotel_agent()
            try:
                hotel_result = await hotel_agent.handle_hotel_query(user_query)
                results.append({
                    'agent': 'Hotel',
                    'result': hotel_result
                })
                print("Hotel Agent completed.")
                print()
            except Exception as e:
                print(f"Error in hotel agent: {e}")
                results.append({
                    'agent': 'Hotel',
                    'result': f"Error: {str(e)}"
                })
        
        # Step 4: Transport search (if needed)
        if needs_transport:
            print("Invoking Transport Agent...")
            transport_agent = await self._get_transport_agent()
            try:
                transport_result = await transport_agent.handle_transport_query(user_query)
                results.append({
                    'agent': 'Transport',
                    'result': transport_result
                })
                print("Transport Agent completed.")
                print()
            except Exception as e:
                print(f"Error in transport agent: {e}")
                results.append({
                    'agent': 'Transport',
                    'result': f"Error: {str(e)}"
                })
        
        # Step 5: Aggregate results
        if not results:
            return "I couldn't determine what you're looking for. Please provide more details about your travel needs (e.g., destinations, flights, dates)."
        
        # Build consolidated response
        response_parts = []
        response_parts.append("=" * 80)
        response_parts.append("Travel Planning Results")
        response_parts.append("=" * 80)
        response_parts.append("")
        
        for result in results:
            response_parts.append(f"--- {result['agent']} Agent Results ---")
            response_parts.append(result['result'])
            response_parts.append("")
        
        response_parts.append("=" * 80)
        
        return "\n".join(response_parts)
    
    async def cleanup(self):
        """Clean up all agent resources."""
        if self.destination_agent:
            await self.destination_agent.cleanup()
            self.destination_agent = None
        
        if self.flight_agent:
            await self.flight_agent.cleanup()
            self.flight_agent = None
        
        if self.hotel_agent:
            await self.hotel_agent.cleanup()
            self.hotel_agent = None
        
        if self.transport_agent:
            await self.transport_agent.cleanup()
            self.transport_agent = None
    
    async def discover_destinations_structured(
        self,
        trip_request: TripRequest
    ) -> List[Destination]:
        """
        Discover destinations using structured trip request.
        
        Args:
            trip_request: Structured trip request with all user preferences
        
        Returns:
            List of Destination objects
        """
        destination_agent = await self._get_destination_agent()
        return await destination_agent.discover_destinations_structured(trip_request)

