"""
Flight Agent

Specialized agent for flight search, pricing, and booking operations.
Uses mcp-flights MCP server to interact with Amadeus flight APIs.

This agent uses GuardiAgent MCP Sandbox (via mcp_sandbox_openai_sdk) to securely
run MCP servers in Docker containers with restricted permissions.

Uses OpenAI's structured output feature (output_type) for reliable JSON responses.
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, Type, List

# Import comprehensive logging
from utils.logging_config import (
    get_agent_logger,
    get_mcp_logger,
    log_agent_input,
    log_agent_output,
    log_agent_state,
    log_mcp_request,
    log_mcp_response
)

# Get specialized loggers
logger = get_agent_logger('flight')
mcp_logger = get_mcp_logger('flights')

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(backend_dir, '..', 'python-mcp-sandbox-openai-sdk-main', 'src'))
sys.path.insert(0, backend_dir)

# Import from openai-agents package
from agents import Agent, Runner
from mcp_sandbox_openai_sdk import (
    DevMCPManifest,
    MCPServers,
    Permission,
    Registry,
    SandboxedMCPStdio,
)
from pydantic import BaseModel

from config import Config
from .mcp_container_helper import ensure_container_running
from .base_agent import BaseAgent

from models import (
    FlightInput,
    FlightOutput,
    FlightOption,
    AgentResult,
    AgentType,
    ValidationResult,
)


class FlightAgent(BaseAgent):
    """
    Agent specialized in flight operations.
    
    Handles flight search, pricing, booking, and route queries
    using the mcp-flights MCP server.
    
    Uses structured output (output_type=FlightOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the flight agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
        """
        super().__init__(model=model)
        self._agent: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
    
    @property
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        return AgentType.FLIGHT
    
    def get_input_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for input validation."""
        return FlightInput
    
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for output validation."""
        return FlightOutput
    
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute flight search based on input parameters.
        
        Uses structured output - the LLM returns a FlightOutput directly.
        
        Args:
            params: Dictionary matching FlightInput schema
        
        Returns:
            AgentResult with flight search results
        """
        try:
            log_agent_input(logger, "FlightAgent", "execute", params)
            log_agent_state(logger, "FlightAgent", "EXECUTING", {"params": params})
            
            # Extract parameters
            origin = params.get("origin", "")
            destination = params.get("destination", "")
            departure_date = params.get("departure_date", "")
            return_date = params.get("return_date")
            adults = params.get("adults", 1)
            max_price = params.get("max_price")
            
            logger.info("=" * 60)
            logger.info("🛫 FLIGHT AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            logger.info(f"  Origin:      {origin}")
            logger.info(f"  Destination: {destination}")
            logger.info(f"  Departure:   {departure_date}")
            logger.info(f"  Return:      {return_date or 'One-way'}")
            logger.info(f"  Adults:      {adults}")
            logger.info(f"  Max Price:   ${max_price}" if max_price else "  Max Price:   No limit")
            logger.info("-" * 60)
            
            # Call the search method - returns structured FlightOutput
            logger.info("📡 Calling search_flights (structured output)...")
            flight_output = await self.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                max_price=max_price
            )
            
            logger.info("-" * 60)
            logger.info(f"✅ Received {len(flight_output.flights)} flights (structured)")
            
            for i, flight in enumerate(flight_output.flights[:3]):  # Log first 3
                logger.info(f"  Flight {i+1}: {flight.airline} - ${flight.price}")
            
            logger.info("=" * 60)
            
            # Convert FlightOutput to dict for AgentResult
            flights_data = [flight.model_dump() for flight in flight_output.flights]
            
            result_data = {
                "flights": flights_data,
                "search_summary": flight_output.search_summary
            }
            
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data=result_data,
                validation=ValidationResult(is_valid=True)
            )
            
            log_agent_output(logger, "FlightAgent", "execute", result_data, success=True)
            log_agent_state(logger, "FlightAgent", "COMPLETED", {"flights_found": len(flights_data)})
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in flight agent execution: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback:\n{error_trace}")
            
            error_result = AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )
            
            log_agent_output(logger, "FlightAgent", "execute", {"error": str(e)}, success=False)
            log_agent_state(logger, "FlightAgent", "FAILED", {"error": str(e)})
            
            return error_result
    
    async def _create_agent(self) -> Agent:
        """Create the agent with mcp-flights MCP server and structured output."""
        if self._agent is not None:
            logger.info("♻️  Reusing existing Flight Agent instance")
            return self._agent
        
        logger.info("🔧 Creating new Flight Agent (with structured output)...")
        
        # Ensure long-running container is running (started via Makefile)
        logger.info(f"🐳 Checking container: {Config.MCP_FLIGHTS_CONTAINER}")
        ensure_container_running(Config.MCP_FLIGHTS_CONTAINER)
        
        # Get runtime permissions
        runtime_permissions = Config.get_runtime_permissions()
        logger.info(f"🔐 Runtime permissions configured: {len(runtime_permissions)} rules")
        
        # Create flights MCP manifest
        logger.info("📦 Creating MCP flights manifest...")
        flights_manifest = DevMCPManifest(
            name="mcp-flights",
            description="MCP server for flight search, pricing, and booking via Amadeus APIs",
            registry=Registry.PYPI,
            package_name="amadeus",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_FLIGHTS_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True
        )
        
        # Create and start MCP servers (use long-running containers)
        logger.info("🚀 Starting MCP server connection...")
        self._servers = MCPServers(
            SandboxedMCPStdio(
                manifest=flights_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=300,
            )
        )
        
        logger.info("⏳ Initializing MCP server (this may take a moment)...")
        await self._servers.__aenter__()
        logger.info("✅ MCP server connected!")
        
        logger.info(f"🤖 Creating LLM agent with model: {self.model}")
        logger.info("📋 Using structured output: FlightOutput")
        
        # Create agent WITH structured output_type
        self._agent = Agent(
            name="Flight Agent",
            model=self.model,
            mcp_servers=self._servers,
            output_type=FlightOutput,  # Structured output - LLM returns typed JSON
        )
        
        logger.info("✅ Flight Agent ready!")
        return self._agent
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        max_price: Optional[float] = None
    ) -> FlightOutput:
        """
        Search for flights between origin and destination.
        
        Uses structured output - returns FlightOutput directly.
        
        Args:
            origin: Origin airport code (e.g., "ZRH")
            destination: Destination airport code (e.g., "LIS")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            adults: Number of adult passengers (default: 1)
            max_price: Optional maximum price filter
        
        Returns:
            FlightOutput with structured flight data
        """
        import time
        start_time = time.time()
        
        log_agent_state(logger, "FlightAgent", "SEARCHING_FLIGHTS", {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "max_price": max_price
        })
        
        logger.info("🔄 search_flights() called")
        logger.debug(f"Creating agent instance...")
        agent = await self._create_agent()
        logger.debug(f"Agent instance created")
        
        prompt = f"""Search for flights from {origin} to {destination}.

Search Parameters:
- Departure Date: {departure_date}
"""
        
        if return_date:
            prompt += f"- Return Date: {return_date}\n"
        
        prompt += f"- Passengers: {adults} adult(s)\n"
        
        if max_price:
            prompt += f"- Maximum Price: ${max_price} (filter out flights above this price)\n"
        
        prompt += """
Instructions:
1. Use the search_flights tool to find available flights
2. Extract the flight information and return it in the structured format
3. For each flight, provide:
   - id: The offer ID from the API
   - airline: The airline code (e.g., "LX", "UA")
   - departure_time: Time in HH:MM format (extract from first segment's departure time)
   - arrival_time: Time in HH:MM format (extract from last segment of outbound itinerary's arrival time)
   - departure_airport: Origin airport code (from first segment)
   - arrival_airport: Destination airport code (from last segment of outbound itinerary)
   - duration: Total flight duration (e.g., "2h 30m")
   - stops: Number of stops (0 for direct)
   - price: Total price as a number
   - currency: Currency code (e.g., "CHF")
   - flight_number: Use the "flight_number" field directly from the API response (already formatted, e.g., "KL1005")
   - return_flight_number: Use the "return_flight_number" field directly from the API response if this is a round trip (e.g., "KL1006")
   - return_departure_time: Return departure time in HH:MM format (extract from first segment of return itinerary, if round trip)
   - return_arrival_time: Return arrival time in HH:MM format (extract from last segment of return itinerary, if round trip)
   - return_departure_airport: Return departure airport code (from first segment of return itinerary, if round trip)
   - return_arrival_airport: Return arrival airport code (from last segment of return itinerary, if round trip)
4. The API response includes formatted flight numbers in the "flight_number" and "return_flight_number" fields - use these directly.
5. For round trips, the response has two itineraries: first is outbound, second is return. Extract return flight details from the second itinerary.
6. Include at least the top 5 cheapest options that match the criteria
7. Provide a brief search_summary describing what was found
"""

        logger.info("📤 Sending prompt to LLM (structured output mode)...")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.debug(f"Full prompt:\n{prompt}")
        
        log_agent_state(logger, "FlightAgent", "CALLING_LLM", {
            "prompt_length": len(prompt),
            "model": self.model
        })
        
        logger.info("⏳ Waiting for LLM response...")
        logger.debug("LLM will call MCP tools - MCP logs will show tool calls")
        
        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        elapsed = time.time() - start_time
        logger.info(f"⏱️  LLM response received in {elapsed:.2f}s")
        logger.debug(f"Raw result type: {type(result)}")
        logger.debug(f"Result has final_output: {hasattr(result, 'final_output')}")
        
        # With output_type=FlightOutput, result.final_output is already the typed object
        # If it's a string (fallback), we need to handle it
        if isinstance(result.final_output, FlightOutput):
            logger.info(f"✅ Structured output received: {len(result.final_output.flights)} flights")
            return result.final_output
        elif isinstance(result.final_output, str):
            # Fallback: try to parse as JSON if string returned
            logger.warning("⚠️ Received string instead of structured output, attempting to parse...")
            try:
                # Try to extract JSON from the string
                output_str = result.final_output.strip()
                if output_str.startswith("```json"):
                    output_str = output_str[7:]
                if output_str.startswith("```"):
                    output_str = output_str[3:]
                if output_str.endswith("```"):
                    output_str = output_str[:-3]
                output_str = output_str.strip()
                
                data = json.loads(output_str)
                return FlightOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return FlightOutput(flights=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(result.final_output)}")
            try:
                if hasattr(result.final_output, 'model_dump'):
                    return FlightOutput(**result.final_output.model_dump())
                elif isinstance(result.final_output, dict):
                    return FlightOutput(**result.final_output)
                else:
                    return FlightOutput(flights=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return FlightOutput(flights=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def handle_flight_query(self, query: str) -> FlightOutput:
        """
        Handle a general flight-related query.
        
        Args:
            query: User's flight-related query
        
        Returns:
            FlightOutput with structured response
        """
        agent = await self._create_agent()
        
        prompt = f"""You are a flight booking assistant. Help the user with their flight request.

User Query: {query}

Use the available flight tools to:
- Search for flights
- Get pricing information
- Check airline routes
- Convert city/airport names to IATA codes if needed
- Provide booking assistance

Return the results in the structured format with flights and a search_summary."""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        # Handle structured output
        if isinstance(result.final_output, FlightOutput):
            return result.final_output
        else:
            return FlightOutput(flights=[], search_summary=str(result.final_output))
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            await self._servers.__aexit__(None, None, None)
            self._servers = None
        self._agent = None
