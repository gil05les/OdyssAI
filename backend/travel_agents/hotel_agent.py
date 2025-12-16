"""
Hotel Agent

Specialized agent for hotel search, pricing, and booking operations.
Uses mcp-hotels MCP server to interact with Amadeus hotel APIs.

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
logger = get_agent_logger('hotel')
mcp_logger = get_mcp_logger('hotels')

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
    HotelInput,
    HotelOutput,
    HotelOption,
    AgentResult,
    AgentType,
    ValidationResult,
)


class HotelAgent(BaseAgent):
    """
    Agent specialized in hotel operations.
    
    Handles hotel search, pricing, and booking queries
    using the mcp-hotels MCP server.
    
    Uses structured output (output_type=HotelOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the hotel agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
        """
        super().__init__(model=model)
        self._agent: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
    
    @property
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        return AgentType.HOTEL
    
    def get_input_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for input validation."""
        return HotelInput
    
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for output validation."""
        return HotelOutput
    
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute hotel search based on input parameters.
        
        Uses structured output - the LLM returns a HotelOutput directly.
        
        Args:
            params: Dictionary matching HotelInput schema
        
        Returns:
            AgentResult with hotel search results
        """
        try:
            log_agent_input(logger, "HotelAgent", "execute", params)
            log_agent_state(logger, "HotelAgent", "EXECUTING", {"params": params})
            
            # Extract parameters
            city_code = params.get("city_code", "")
            check_in = params.get("check_in", "")
            check_out = params.get("check_out", "")
            guests = params.get("guests", 1)
            max_price_per_night = params.get("max_price_per_night")
            
            logger.info("=" * 60)
            logger.info("🏨 HOTEL AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            logger.info(f"  City:        {city_code}")
            logger.info(f"  Check-in:    {check_in}")
            logger.info(f"  Check-out:   {check_out}")
            logger.info(f"  Guests:      {guests}")
            logger.info(f"  Max Price:   ${max_price_per_night}/night" if max_price_per_night else "  Max Price:   No limit")
            logger.info("-" * 60)
            
            # Call the search method - returns structured HotelOutput
            logger.info("📡 Calling search_hotels (structured output)...")
            hotel_output = await self.search_hotels(
                city_code=city_code,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                max_price_per_night=max_price_per_night
            )
            
            logger.info("-" * 60)
            logger.info(f"✅ Received {len(hotel_output.hotels)} hotels (structured)")
            
            for i, hotel in enumerate(hotel_output.hotels[:3]):  # Log first 3
                logger.info(f"  Hotel {i+1}: {hotel.name} - ${hotel.price_per_night}/night")
            
            logger.info("=" * 60)
            
            # Convert HotelOutput to dict for AgentResult
            hotels_data = [hotel.model_dump() for hotel in hotel_output.hotels]
            
            result_data = {
                "hotels": hotels_data,
                "search_summary": hotel_output.search_summary
            }
            
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data=result_data,
                validation=ValidationResult(is_valid=True)
            )
            
            log_agent_output(logger, "HotelAgent", "execute", result_data, success=True)
            log_agent_state(logger, "HotelAgent", "COMPLETED", {"hotels_found": len(hotels_data)})
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in hotel agent execution: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback:\n{error_trace}")
            
            error_result = AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )
            
            log_agent_output(logger, "HotelAgent", "execute", {"error": str(e)}, success=False)
            log_agent_state(logger, "HotelAgent", "FAILED", {"error": str(e)})
            
            return error_result
    
    async def _create_agent(self) -> Agent:
        """Create the agent with mcp-hotels MCP server and structured output."""
        if self._agent is not None:
            logger.info("♻️  Reusing existing Hotel Agent instance")
            return self._agent
        
        logger.info("🔧 Creating new Hotel Agent (with structured output)...")
        
        # Ensure long-running container is running (started via Makefile)
        logger.info(f"🐳 Checking container: {Config.MCP_HOTELS_CONTAINER}")
        ensure_container_running(Config.MCP_HOTELS_CONTAINER)
        
        # Get runtime permissions
        runtime_permissions = Config.get_runtime_permissions()
        logger.info(f"🔐 Runtime permissions configured: {len(runtime_permissions)} rules")
        
        # Create hotels MCP manifest
        logger.info("📦 Creating MCP hotels manifest...")
        hotels_manifest = DevMCPManifest(
            name="mcp-hotels",
            description="MCP server for hotel search, pricing, and booking via Amadeus APIs",
            registry=Registry.PYPI,
            package_name="amadeus",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_HOTELS_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True
        )
        
        # Create and start MCP servers (use long-running containers)
        logger.info("🚀 Starting MCP server connection...")
        self._servers = MCPServers(
            SandboxedMCPStdio(
                manifest=hotels_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=300,
            )
        )
        
        logger.info("⏳ Initializing MCP server (this may take a moment)...")
        await self._servers.__aenter__()
        logger.info("✅ MCP server connected!")
        
        logger.info(f"🤖 Creating LLM agent with model: {self.model}")
        logger.info("📋 Using structured output: HotelOutput")
        
        # Create agent WITH structured output_type
        self._agent = Agent(
            name="Hotel Agent",
            model=self.model,
            mcp_servers=self._servers,
            output_type=HotelOutput,  # Structured output - LLM returns typed JSON
        )
        
        logger.info("✅ Hotel Agent ready!")
        return self._agent
    
    async def search_hotels(
        self,
        city_code: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
        max_price_per_night: Optional[float] = None
    ) -> HotelOutput:
        """
        Search for hotels in a specific city.
        
        Uses structured output - returns HotelOutput directly.
        
        Args:
            city_code: IATA city code (e.g., "LIS" for Lisbon)
            check_in: Check-in date in YYYY-MM-DD format
            check_out: Check-out date in YYYY-MM-DD format
            guests: Number of guests (default: 1)
            max_price_per_night: Optional maximum price per night filter
        
        Returns:
            HotelOutput with structured hotel data
        """
        import time
        start_time = time.time()
        
        log_agent_state(logger, "HotelAgent", "SEARCHING_HOTELS", {
            "city_code": city_code,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "max_price_per_night": max_price_per_night
        })
        
        logger.info("🔄 search_hotels() called")
        logger.debug(f"Creating agent instance...")
        agent = await self._create_agent()
        logger.debug(f"Agent instance created")
        
        prompt = f"""Search for hotels in {city_code}.

Search Parameters:
- Check-in Date: {check_in}
- Check-out Date: {check_out}
- Guests: {guests}
"""
        
        if max_price_per_night:
            prompt += f"- Maximum Price per Night: ${max_price_per_night} (filter out hotels above this price per night)\n"
        
        prompt += """
Instructions:
1. Use the search_hotels_in_city tool to find available hotels
2. The tool returns a response with a "hotel_offers" array. Each offer has these fields:
   - offer_id: Unique identifier for the offer
   - hotel_id: Hotel identifier
   - hotel_name: Name of the hotel
   - hotel_rating: Hotel rating (if available from Amadeus API, otherwise null)
   - image_url: URL to hotel image (already generated)
   - price_total: Total price for the entire stay
   - price_per_night: Price per night (already calculated)
   - currency: Currency code (e.g., "CHF", "EUR")
   - room_type: Type/category of room
   - room_description: Description of the room
   - check_in: Check-in date
   - check_out: Check-out date
   - guests: Number of guests
   - nights: Number of nights
3. Extract the hotel information and return it in the structured HotelOutput format
4. For each hotel offer, map the fields as follows:
   - id: Use the offer_id from the API response
   - name: Use hotel_name from the API response
   - address: Use room_description if available, otherwise create a location description like "Located in {city_code}"
   - rating: Use hotel_rating from the API response if available. If not available, estimate based on hotel name/brand, price point, location, and amenities. For example: luxury brands (Ritz, Four Seasons, Mandarin Oriental) = 4.5-5.0, mid-range chains (Hilton, Marriott) = 4.0-4.5, budget chains = 3.5-4.0. Higher price per night generally indicates better rating.
   - review_count: If rating is available from API, estimate review count based on rating (e.g., rating 4.5 -> ~150-300 reviews, rating 4.0 -> ~100-200 reviews, rating 3.5 -> ~50-100 reviews). If rating is also not available, estimate both rating and review count together using the same contextual clues. Well-known hotel chains typically have 100-500 reviews, independent hotels may have 20-100 reviews.
   - image_url: Use the image_url from the API response
   - price_per_night: Use price_per_night from the API response as a number (float)
   - total_price: Use price_total from the API response as a number (float)
   - currency: Use currency from the API response (e.g., "CHF", "EUR")
   - amenities: Extract from room_description if it mentions amenities, otherwise use common amenities like ["WiFi", "Air Conditioning"]
5. Include at least the top 5 best options that match the criteria (prefer lower prices if max_price_per_night is set)
6. Provide a brief search_summary describing what was found, including the city, number of hotels found, and price range

IMPORTANT: You must call the search_hotels_in_city tool with the exact parameters provided above. The tool requires city_code, check_in, check_out, and guests parameters.
"""

        logger.info("📤 Sending prompt to LLM (structured output mode)...")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.debug(f"Full prompt:\n{prompt}")
        
        log_agent_state(logger, "HotelAgent", "CALLING_LLM", {
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
        
        # With output_type=HotelOutput, result.final_output is already the typed object
        # If it's a string (fallback), we need to handle it
        if isinstance(result.final_output, HotelOutput):
            logger.info(f"✅ Structured output received: {len(result.final_output.hotels)} hotels")
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
                return HotelOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return HotelOutput(hotels=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(result.final_output)}")
            try:
                if hasattr(result.final_output, 'model_dump'):
                    return HotelOutput(**result.final_output.model_dump())
                elif isinstance(result.final_output, dict):
                    return HotelOutput(**result.final_output)
                else:
                    return HotelOutput(hotels=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return HotelOutput(hotels=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def search_hotels_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 1,
        radius: Optional[float] = None
    ) -> HotelOutput:
        """
        Search for hotels near specific coordinates.
        
        Uses structured output - returns HotelOutput directly.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            check_in: Optional check-in date in YYYY-MM-DD format
            check_out: Optional check-out date in YYYY-MM-DD format
            guests: Number of guests (default: 1)
            radius: Optional search radius
        
        Returns:
            HotelOutput with structured hotel data
        """
        agent = await self._create_agent()
        
        prompt = f"""Search for hotels near coordinates {latitude}, {longitude}.
"""
        
        if check_in and check_out:
            prompt += f"Check-in Date: {check_in}\n"
            prompt += f"Check-out Date: {check_out}\n"
        
        prompt += f"Guests: {guests}\n"
        
        if radius:
            prompt += f"Search Radius: {radius} km\n"
        
        prompt += """
Instructions:
1. Search for available hotels in the area
2. Extract the hotel information and return it in the structured format
3. For each hotel, provide:
   - id: The hotel/offer ID
   - name: Hotel name
   - address: Hotel address and distance from coordinates
   - rating: Star rating if available
   - price_per_night: Price per night
   - total_price: Total price for the stay
   - currency: Currency code
   - amenities: List of amenities
4. Include at least the top 5 options
5. Provide a search_summary with location information
"""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        # Handle structured output
        if isinstance(result.final_output, HotelOutput):
            return result.final_output
        else:
            return self._handle_output(result.final_output)
    
    async def handle_hotel_query(self, query: str) -> HotelOutput:
        """
        Handle a general hotel-related query.
        
        Args:
            query: User's hotel-related query
        
        Returns:
            HotelOutput with structured response
        """
        agent = await self._create_agent()
        
        prompt = f"""You are a hotel booking assistant. Help the user with their hotel request.

User Query: {query}

Instructions:
1. Use the available hotel tools to search for hotels:
   - search_hotels_in_city: For searching by city code (IATA code like "LIS", "BCN", "PAR")
   - search_hotels_by_coordinates: For searching by latitude/longitude
   - get_hotel_offer_details: For getting details about a specific offer
2. If the user mentions a city name, you may need to convert it to an IATA city code first
3. Extract hotel information from the tool responses and return it in the structured HotelOutput format
4. For each hotel, provide:
   - id: The offer_id from the API response
   - name: The hotel_name from the API response
   - address: Use room_description or create a location description
   - rating: Set to null (API doesn't provide this)
   - price_per_night: Use price_per_night as a number
   - total_price: Use price_total as a number
   - currency: Use currency code from response
   - amenities: Extract from room_description or use common amenities
5. Include at least the top 5 best options
6. Provide a brief search_summary describing what was found

IMPORTANT: You must call one of the search tools (search_hotels_in_city or search_hotels_by_coordinates) to get hotel data. The tool responses will have a "hotel_offers" array with the hotel information."""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        # Handle structured output
        if isinstance(result.final_output, HotelOutput):
            return result.final_output
        else:
            return self._handle_output(result.final_output)
    
    def _handle_output(self, output: Any) -> HotelOutput:
        """
        Handle the agent output, converting to HotelOutput if needed.
        
        Args:
            output: The raw output from Runner.run
        
        Returns:
            HotelOutput with validated hotels
        """
        # With output_type=HotelOutput, result should already be typed
        if isinstance(output, HotelOutput):
            logger.info(f"✅ Structured output received: {len(output.hotels)} hotels")
            return output
        elif isinstance(output, str):
            # Fallback: try to parse as JSON if string returned
            logger.warning("⚠️ Received string instead of structured output, attempting to parse...")
            try:
                # Try to extract JSON from the string
                output_str = output.strip()
                if output_str.startswith("```json"):
                    output_str = output_str[7:]
                if output_str.startswith("```"):
                    output_str = output_str[3:]
                if output_str.endswith("```"):
                    output_str = output_str[:-3]
                output_str = output_str.strip()
                
                data = json.loads(output_str)
                return HotelOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return HotelOutput(hotels=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(output)}")
            try:
                if hasattr(output, 'model_dump'):
                    return HotelOutput(**output.model_dump())
                elif isinstance(output, dict):
                    return HotelOutput(**output)
                else:
                    return HotelOutput(hotels=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return HotelOutput(hotels=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            await self._servers.__aexit__(None, None, None)
            self._servers = None
        self._agent = None
