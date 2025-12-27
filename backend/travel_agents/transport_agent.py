"""
Transport Agent

Specialized agent for transport options including ride estimates and Google Maps directions.
Uses mcp-transport MCP server to interact with Google Maps APIs.
Note: Uber API integration is disabled (API key not obtainable) - uses LLM fallback for ride estimates.

This agent uses GuardiAgent MCP Sandbox (via mcp_sandbox_openai_sdk) to securely
run MCP servers in Docker containers with restricted permissions.

Uses OpenAI's structured output feature (output_type) for reliable JSON responses.
Includes graceful error handling with LLM fallback for generating estimates when APIs fail.
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
logger = get_agent_logger('transport')
mcp_logger = get_mcp_logger('transport')

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
    TransportInput,
    TransportOutput,
    TransportLegOutput,
    TransportOptionOutput,
    AgentResult,
    AgentType,
    ValidationResult,
)


class TransportAgent(BaseAgent):
    """
    Agent specialized in transport options.
    
    Handles transport search for trip legs including:
    - Airport to Hotel transfers
    - Hotel to activity locations
    - Inter-city transport
    
    Uses mcp-transport MCP server with Google Maps APIs.
    Uber estimates use LLM fallback (Uber API key not obtainable).
    Includes graceful error handling with LLM fallback.
    
    Uses structured output (output_type=TransportOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(self, model: Optional[str] = None, user_id: Optional[int] = None):
        """
        Initialize the transport agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
            user_id: Optional user ID for preference matching
        """
        super().__init__(model=model)
        self._agent: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
        self._user_id = user_id
    
    @property
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        return AgentType.TRANSPORT
    
    def get_input_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for input validation."""
        return TransportInput
    
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for output validation."""
        return TransportOutput
    
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute transport search based on trip context.
        
        Uses structured output - the LLM returns a TransportOutput directly.
        
        Args:
            params: Dictionary matching TransportInput schema
        
        Returns:
            AgentResult with transport search results
        """
        try:
            log_agent_input(logger, "TransportAgent", "execute", params)
            log_agent_state(logger, "TransportAgent", "EXECUTING", {"params": params})
            
            # Extract parameters
            destination_city = params.get("destination_city", "")
            destination_country = params.get("destination_country", "")
            hotel_address = params.get("hotel_address", "")
            airport_code = params.get("airport_code", "")
            itinerary_locations = params.get("itinerary_locations", [])
            arrival_datetime = params.get("arrival_datetime", "")
            departure_datetime = params.get("departure_datetime", "")
            group_size = params.get("group_size", 1)
            
            logger.info("=" * 60)
            logger.info("🚗 TRANSPORT AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            logger.info(f"  Destination: {destination_city}, {destination_country}")
            logger.info(f"  Hotel: {hotel_address}")
            logger.info(f"  Airport: {airport_code}")
            logger.info(f"  Locations: {len(itinerary_locations)} key locations")
            if itinerary_locations:
                logger.info(f"    Location list: {', '.join(itinerary_locations[:5])}{'...' if len(itinerary_locations) > 5 else ''}")
            else:
                logger.warning("    ⚠️  No itinerary locations provided - will only generate airport transfers")
            logger.info(f"  Arrival: {arrival_datetime}")
            logger.info(f"  Departure: {departure_datetime}")
            logger.info("-" * 60)
            
            # Call the search method - returns structured TransportOutput
            logger.info("📡 Calling search_transport_options (structured output)...")
            transport_output = await self.search_transport_options(
                destination_city=destination_city,
                destination_country=destination_country,
                hotel_address=hotel_address,
                airport_code=airport_code,
                itinerary_locations=itinerary_locations,
                arrival_datetime=arrival_datetime,
                departure_datetime=departure_datetime,
                group_size=group_size
            )
            
            logger.info("-" * 60)
            logger.info(f"✅ Received {len(transport_output.legs)} transport legs (structured)")
            
            for i, leg in enumerate(transport_output.legs[:3]):  # Log first 3
                logger.info(f"  Leg {i+1}: {leg.from_location} -> {leg.to_location} ({len(leg.options)} options)")
            
            logger.info("=" * 60)
            
            # Convert TransportOutput to dict for AgentResult
            legs_data = [leg.model_dump() for leg in transport_output.legs]
            
            result_data = {
                "legs": legs_data,
                "search_summary": transport_output.search_summary
            }
            
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data=result_data,
                validation=ValidationResult(is_valid=True)
            )
            
            log_agent_output(logger, "TransportAgent", "execute", result_data, success=True)
            log_agent_state(logger, "TransportAgent", "COMPLETED", {"legs_found": len(legs_data)})
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in transport agent execution: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback:\n{error_trace}")
            
            error_result = AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )
            
            log_agent_output(logger, "TransportAgent", "execute", {"error": str(e)}, success=False)
            log_agent_state(logger, "TransportAgent", "FAILED", {"error": str(e)})
            
            return error_result
    
    async def _create_agent(self) -> Agent:
        """Create the agent with mcp-transport and mcp-preferences MCP servers and structured output."""
        if self._agent is not None:
            logger.info("♻️  Reusing existing Transport Agent instance")
            return self._agent
        
        logger.info("🔧 Creating new Transport Agent (with structured output)...")
        
        # Ensure long-running containers are running (started via Makefile)
        logger.info(f"🐳 Checking container: {Config.MCP_TRANSPORT_CONTAINER}")
        ensure_container_running(Config.MCP_TRANSPORT_CONTAINER)
        logger.info(f"🐳 Checking container: {Config.MCP_PREFERENCES_CONTAINER}")
        ensure_container_running(Config.MCP_PREFERENCES_CONTAINER)
        
        # Get runtime permissions
        runtime_permissions = Config.get_runtime_permissions()
        logger.info(f"🔐 Runtime permissions configured: {len(runtime_permissions)} rules")
        
        # Create transport MCP manifest
        logger.info("📦 Creating MCP transport manifest...")
        transport_manifest = DevMCPManifest(
            name="mcp-transport",
            description="MCP server for transport options including Google Maps directions (Uber uses LLM fallback)",
            registry=Registry.PYPI,
            package_name="requests",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_TRANSPORT_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True
        )
        
        # Create preferences MCP manifest
        logger.info("📦 Creating MCP preferences manifest...")
        preferences_manifest = DevMCPManifest(
            name="mcp-preferences",
            description="MCP server for user preference analysis from trip history",
            registry=Registry.PYPI,
            package_name="sqlalchemy",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_PREFERENCES_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True
        )
        
        # Create list of MCP servers
        servers_list = [
            SandboxedMCPStdio(
                manifest=transport_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=300,
            ),
            SandboxedMCPStdio(
                manifest=preferences_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=300,
                runtime_args=["--network", "odyssai_odyssai-network"],
            )
        ]
        
        # Create and start MCP servers (use long-running containers)
        logger.info("🚀 Starting MCP server connections...")
        self._servers = MCPServers(*servers_list)
        
        logger.info("⏳ Initializing MCP servers (this may take a moment)...")
        await self._servers.__aenter__()
        logger.info("✅ MCP servers connected!")
        
        logger.info(f"🤖 Creating LLM agent with model: {self.model}")
        logger.info("📋 Using structured output: TransportOutput")
        
        # Create agent WITH structured output_type
        self._agent = Agent(
            name="Transport Agent",
            model=self.model,
            mcp_servers=self._servers,
            output_type=TransportOutput,  # Structured output - LLM returns typed JSON
        )
        
        logger.info("✅ Transport Agent ready!")
        return self._agent
    
    async def search_transport_options(
        self,
        destination_city: str,
        destination_country: str,
        hotel_address: str,
        airport_code: str,
        itinerary_locations: List[str],
        arrival_datetime: str,
        departure_datetime: str,
        group_size: int = 1
    ) -> TransportOutput:
        """
        Search for transport options for all trip legs.
        
        Uses structured output - returns TransportOutput directly.
        Includes graceful error handling with LLM fallback.
        
        Args:
            destination_city: Destination city name
            destination_country: Destination country name
            hotel_address: Hotel address
            airport_code: Airport IATA code
            itinerary_locations: List of key locations from itinerary
            arrival_datetime: Arrival date/time
            departure_datetime: Departure date/time
            group_size: Number of travelers
        
        Returns:
            TransportOutput with structured transport data
        """
        import time
        start_time = time.time()
        
        log_agent_state(logger, "TransportAgent", "SEARCHING_TRANSPORT", {
            "destination_city": destination_city,
            "hotel_address": hotel_address,
            "airport_code": airport_code,
            "locations_count": len(itinerary_locations)
        })
        
        logger.info("🔄 search_transport_options() called")
        logger.debug(f"Creating agent instance...")
        agent = await self._create_agent()
        logger.debug(f"Agent instance created")
        
        # Build locations list for prompt
        locations_text = "\n".join([f"  - {loc}" for loc in itinerary_locations]) if itinerary_locations else "  (none specified)"
        
        # Build preferences section if user_id is provided
        preferences_section = ""
        if self._user_id:
            preferences_section = f"""
STEP 1 - Get User Preferences:
- Call get_transport_preferences with user_id={self._user_id}
- Note their preferred transport modes (uber, transit, walking, taxi), price sensitivity, and typical choices
- If has_preference is false, proceed without preference matching

"""
        
        prompt = f"""Analyze this trip and find transport options for ALL legs.
{preferences_section}

CRITICAL REQUIREMENT: You must create transport legs for:
1. Airport transfers (arrival and departure)
2. EACH itinerary location provided (both to and from hotel)

Trip Context:
- Destination: {destination_city}, {destination_country}
- Hotel: {hotel_address}
- Airport: {airport_code}
- Key locations from itinerary ({len(itinerary_locations)} locations):
{locations_text}
- Arrival: {arrival_datetime}
- Departure: {departure_datetime}
- Group size: {group_size} traveler(s)

Instructions:
1. First, use geocode_location to get coordinates for key locations:
   - Hotel address: {hotel_address}
   - Airport: Use "{airport_code} Airport" or search for airport in {destination_city}, {destination_country}
   - For EACH itinerary location, geocode with city/country context:
     * Format: "[location name], {destination_city}, {destination_country}"
     * Example: If location is "Eiffel Tower" and destination is "Paris, France", geocode "Eiffel Tower, Paris, France"
     * This ensures accurate geocoding and prevents confusion with similarly named places in other cities

2. Identify ALL transport legs needed (REQUIRED - do not skip any):
   - Airport to Hotel (arrival transfer) - REQUIRED
   - Hotel to Airport (departure transfer) - REQUIRED
   - For EACH key location in the itinerary, create TWO legs:
     * Hotel to [location name] - REQUIRED for each itinerary location
     * [location name] to Hotel - REQUIRED for each itinerary location (return trip)
   
   IMPORTANT: If itinerary_locations contains locations, you MUST create transport legs for ALL of them.
   Do not skip itinerary locations even if you only have airport transfers.

3. For geocoding itinerary locations, ALWAYS include city and country:
   - When calling geocode_location for an itinerary location, use format: "[location name], {destination_city}, {destination_country}"
   - Example: For "Eiffel Tower" in Paris, geocode "Eiffel Tower, Paris, France"
   - This ensures you get the correct location and not a similarly named place in another city
   - If geocoding fails for a location name alone, retry with city/country context: "[location name], {destination_city}, {destination_country}"

4. For EACH leg, call these tools IN PARALLEL:
   - get_uber_estimate (if coordinates available from geocoding)
   - get_directions_transit (for public transport)
   - get_directions_walking (only if distance < 2km)
   - get_directions_driving (for taxi estimates)

IMPORTANT - Error Handling:
- If a tool returns success=False, DO NOT fail the entire request
- Instead, use your knowledge to GENERATE a reasonable estimate
- For LLM-generated options, set source="llm" (not "api")
- For API-sourced options, set source="api"
- Base estimates on:
  * Typical taxi rates: ~$2-3/km + $3-5 base fare
  * Walking speed: ~5km/h
  * Public transit: ~$2-5 per trip, 30-60 min typical
  * Distance between locations (use geocoding results if available)
  * Local pricing in {destination_country}

5. Return ALL options (both API and LLM-generated) in TransportOutput format
6. Each option MUST have source="api" or source="llm" to indicate origin
7. Format options with:
   - id: unique identifier
   - type: "uber", "transit", "walking", "driving", or "taxi"
   - name: descriptive name (e.g., "UberX", "Metro Line 1", "Walking", "Taxi")
   - duration: human-readable (e.g., "25 min", "1h 15m")
   - duration_seconds: numeric seconds
   - price: numeric price (if available)
   - price_range: string range (e.g., "$15-20") if price varies
   - currency: currency code (e.g., "USD", "EUR", "CHF")
   - distance: distance text (if available)
   - steps: list of route steps (for transit/walking)
   - icon: emoji icon (🚕 for taxi, 🚗 for uber, 🚌 for transit, 🚶 for walking)
   - source: "api" or "llm"
"""
        
        # Add preference matching fields if user_id is provided
        if self._user_id:
            prompt += """   - preference_match: Object with preference matching info (if user preferences were found):
     * mode_match: true if transport type matches user's preferred modes
     * price_match: true if price is within user's typical range based on price_sensitivity
     * reasons: List of human-readable strings explaining WHY this matches (e.g., "You typically prefer transit", "Price within your budget")
   - preference_score: 0-100 score based on preference matches (50 points each for mode and price)
"""
        
        prompt += """

8. Create TransportLegOutput for each leg with:
   - id: unique leg identifier
   - from_location: origin name
   - to_location: destination name
   - options: list of TransportOptionOutput

9. Provide a search_summary describing what was found, including which options are API-sourced vs LLM-generated.

10. VALIDATION CHECK BEFORE RETURNING:
- If itinerary_locations has {len(itinerary_locations)} location(s), you MUST have created {len(itinerary_locations) * 2} legs (to and from each location) PLUS 2 airport legs = {len(itinerary_locations) * 2 + 2} total legs minimum
- If itinerary_locations is empty, you should have 2 legs (airport to hotel, hotel to airport)
- Verify every location in itinerary_locations has corresponding transport legs
"""
        
        logger.info("📤 Sending prompt to LLM (structured output mode)...")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.debug(f"Full prompt:\n{prompt}")
        
        log_agent_state(logger, "TransportAgent", "CALLING_LLM", {
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
        
        # With output_type=TransportOutput, result.final_output is already the typed object
        # If it's a string (fallback), we need to handle it
        if isinstance(result.final_output, TransportOutput):
            logger.info(f"✅ Structured output received: {len(result.final_output.legs)} legs")
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
                return TransportOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return TransportOutput(legs=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(result.final_output)}")
            try:
                if hasattr(result.final_output, 'model_dump'):
                    return TransportOutput(**result.final_output.model_dump())
                elif isinstance(result.final_output, dict):
                    return TransportOutput(**result.final_output)
                else:
                    return TransportOutput(legs=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return TransportOutput(legs=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            await self._servers.__aexit__(None, None, None)
            self._servers = None
        self._agent = None
