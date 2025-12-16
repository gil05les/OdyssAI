"""
Destination Search Agent

Discovers destinations based on user preferences using LLM reasoning.
Can suggest destinations like "beach destinations", "mountain getaways", "cultural cities", etc.

This agent uses GuardiAgent MCP Sandbox (via mcp_sandbox_openai_sdk) to securely
run MCP servers in Docker containers with restricted permissions when accessing flight tools.

Uses OpenAI's structured output feature (output_type) for reliable JSON responses.
"""

import os
import sys
import json
import logging
from typing import Optional, List, Dict, Any, Type

# Configure logging
logger = logging.getLogger(__name__)

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
    DomainPort,
)
from pydantic import BaseModel

from config import Config
from .mcp_container_helper import ensure_container_running
from .base_agent import BaseAgent

# Import models after adding backend_dir to path
from models import (
    Destination,
    TripRequest,
    DestinationInput,
    DestinationOutput,
    AgentResult,
    AgentType,
    ValidationResult,
)


class DestinationAgent(BaseAgent):
    """
    Agent specialized in discovering destinations based on user preferences.
    
    Uses LLM reasoning to suggest destinations and can optionally use
    autocomplete tools to get IATA codes for cities/airports.
    
    Uses structured output (output_type=DestinationOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        use_flights_mcp: bool = True,
        use_geo_mcp: bool = True
    ):
        """
        Initialize the destination agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
            use_flights_mcp: Whether to use mcp-flights for IATA code conversion
            use_geo_mcp: Whether to use mcp-geo-destinations for country info and POIs
        """
        super().__init__(model=model)
        self.use_flights_mcp = use_flights_mcp
        self.use_geo_mcp = use_geo_mcp
        self._agent: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
    
    @property
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        return AgentType.DESTINATION
    
    def get_input_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for input validation."""
        return DestinationInput
    
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for output validation."""
        return DestinationOutput
    
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute destination discovery based on input parameters.
        
        Uses structured output - the LLM returns a DestinationOutput directly.
        
        Args:
            params: Dictionary matching DestinationInput schema
        
        Returns:
            AgentResult with discovered destinations
        """
        try:
            # Convert params to TripRequest for backward compatibility
            trip_request = TripRequest(
                origin=params.get("origin", ""),
                destinations=params.get("destinations", []),
                surprise_me=params.get("surprise_me", True),
                date_ranges=params.get("date_ranges", []),
                duration=params.get("duration", (1, 14)),
                traveler_type=params.get("traveler_type", "solo"),
                group_size=params.get("group_size", 1),
                budget=params.get("budget", (0, 10000)),
                accommodation=params.get("accommodation"),
                experiences=params.get("experiences", []),
                environments=params.get("environments", []),
                climate=params.get("climate"),
                trip_vibe=params.get("trip_vibe"),
                distance_preference=params.get("distance_preference"),
                trip_purpose=params.get("trip_purpose"),
            )
            
            logger.info("=" * 60)
            logger.info("🌍 DESTINATION AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            
            # Call the structured discovery method
            destination_output = await self.discover_destinations_structured(trip_request)
            
            logger.info(f"✅ Received {len(destination_output.destinations)} destinations")
            
            # Convert to dict format for AgentResult
            destinations_data = [dest.model_dump() for dest in destination_output.destinations]
            
            return AgentResult(
                agent_type=self.agent_type,
                success=True,
                data={"destinations": destinations_data},
                validation=ValidationResult(is_valid=True)
            )
            
        except Exception as e:
            logger.error(f"Error in destination agent execution: {e}")
            import traceback
            traceback.print_exc()
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )
    
    async def _create_agent(self) -> Agent:
        """Create the agent with appropriate MCP servers and structured output."""
        if self._agent is not None:
            return self._agent
        
        logger.info("Creating destination agent with MCP servers (structured output)...")
        logger.info(f"MCP_FLIGHTS_PATH: {Config.MCP_FLIGHTS_PATH}")
        logger.info(f"MCP_GEO_PATH: {Config.MCP_GEO_PATH}")
        logger.info(f"HOST_PROJECT_ROOT: {os.getenv('HOST_PROJECT_ROOT', 'not set')}")
        
        servers_list = []
        runtime_permissions = Config.get_runtime_permissions()
        
        # Add flights MCP for IATA code conversion
        if self.use_flights_mcp:
            # Ensure long-running container is running (started via Makefile)
            logger.info(f"Checking if container {Config.MCP_FLIGHTS_CONTAINER} is running...")
            ensure_container_running(Config.MCP_FLIGHTS_CONTAINER)
            
            amadeus_domain = Config.get_amadeus_domain()
            
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
            
            servers_list.append(
                SandboxedMCPStdio(
                    manifest=flights_manifest,
                    runtime_permissions=runtime_permissions,
                    remove_container_after_run=False,
                    client_session_timeout_seconds=300,
                )
            )
        
        # Add geo-destinations MCP for country info and POIs
        if self.use_geo_mcp:
            # Ensure long-running container is running (started via Makefile)
            ensure_container_running(Config.MCP_GEO_CONTAINER)
            
            # Manifest permissions (Permission enum values)
            geo_manifest_permissions = [
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ]
            
            # Runtime permissions (RuntimePermission objects like DomainPort, EnvironmentVariable)
            # Note: OpenWeatherMap is NOT included - temperature is predicted by the LLM
            geo_runtime_permissions = [
                # PyPI access for package installation
                DomainPort(domain='pypi.org', port=443),
                DomainPort(domain='files.pythonhosted.org', port=443),
                # API access
                DomainPort(domain='restcountries.com', port=443),
            ]
            
            geo_manifest = DevMCPManifest(
                name="mcp-geo-destinations",
                description="MCP server for geographical destination information via RestCountries, OpenWeatherMap, and Amadeus APIs",
                registry=Registry.PYPI,
                package_name="amadeus",
                permissions=geo_manifest_permissions,
                code_mount=Config.MCP_GEO_PATH,
                exec_command="bash /sandbox/start.sh",
                preinstalled=True
            )
            
            servers_list.append(
                SandboxedMCPStdio(
                    manifest=geo_manifest,
                    runtime_permissions=geo_runtime_permissions,
                    remove_container_after_run=False,
                    client_session_timeout_seconds=300,
                )
            )
        
        if servers_list:
            logger.info(f"Initializing {len(servers_list)} MCP server(s)...")
            self._servers = MCPServers(*servers_list)
            try:
                await self._servers.__aenter__()
                logger.info("MCP servers initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MCP servers: {e}")
                import traceback
                traceback.print_exc()
                raise
            agent_servers = self._servers
        else:
            logger.info("No MCP servers configured")
            agent_servers = []  # Empty list instead of None
        
        logger.info("📋 Using structured output: DestinationOutput")
        
        # Create agent WITH structured output_type
        self._agent = Agent(
            name="Destination Search Agent",
            model=self.model,
            mcp_servers=agent_servers,
            output_type=DestinationOutput,  # Structured output - LLM returns typed JSON
        )
        
        return self._agent
    
    async def discover_destinations(
        self,
        user_query: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> DestinationOutput:
        """
        Discover destinations based on user preferences.
        
        Uses structured output - returns DestinationOutput directly.
        
        Args:
            user_query: User's query about desired destinations
            preferences: Optional structured preferences (e.g., {"type": "beach", "budget": "moderate"})
        
        Returns:
            DestinationOutput with destination suggestions
        """
        agent = await self._create_agent()
        
        # Build the prompt for destination discovery
        prompt = f"""You are a travel destination expert. Based on the user's request, suggest relevant travel destinations.

User Request: {user_query}

"""
        
        if preferences:
            prompt += f"Additional Preferences: {preferences}\n\n"
        
        prompt += """Please provide 3-5 destinations. For each destination include:
- id: A unique identifier (e.g., "dest-1")
- name: City name
- country: Country name
- description: Brief description of why this destination is great
- match_reason: Why it matches the user's preferences
- temp_range: Temperature range in format "min-max°C" (e.g., "15-25°C") - PREDICT this directly from your climate knowledge
- iata_code: The main airport IATA code

IMPORTANT: Do NOT use any weather API tools. Predict temperatures directly from your knowledge.
Note: Do NOT include an "image" field - images will be fetched automatically."""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        return self._handle_output(result.final_output)
    
    async def discover_destinations_structured(
        self,
        trip_request: TripRequest
    ) -> DestinationOutput:
        """
        Discover destinations based on structured trip request and return typed results.
        
        Uses structured output - returns DestinationOutput directly.
        
        Args:
            trip_request: Structured trip request with all user preferences
        
        Returns:
            DestinationOutput with destinations matching frontend interface
        """
        agent = await self._create_agent()
        
        # Format date ranges for the prompt
        date_ranges_str = ""
        if trip_request.date_ranges:
            for i, dr in enumerate(trip_request.date_ranges):
                from_date = dr.get("from", "")
                to_date = dr.get("to", "")
                if from_date and to_date:
                    date_ranges_str += f"  Range {i+1}: {from_date} to {to_date}\n"
        
        # Format new preference fields
        environments_str = ', '.join(trip_request.environments) if trip_request.environments else 'None specified'
        climate_str = trip_request.climate or 'Not specified'
        vibe_str = trip_request.trip_vibe or 'Not specified'
        distance_str = trip_request.distance_preference or 'Not specified'
        purpose_str = trip_request.trip_purpose or 'Not specified'
        
        # Build comprehensive prompt with all user preferences
        prompt = f"""You are a travel destination expert. Based on the user's detailed preferences, suggest 3-5 relevant travel destinations.

USER PREFERENCES:
- Origin: {trip_request.origin}
- Traveler Type: {trip_request.traveler_type} ({trip_request.group_size} travelers)
- Budget Range: ${trip_request.budget[0]:,} - ${trip_request.budget[1]:,}
- Trip Duration: {trip_request.duration[0]}-{trip_request.duration[1]} days
- Preferred Environments: {environments_str}
- Climate Preference: {climate_str}
- Trip Vibe/Pace: {vibe_str}
- Distance Preference: {distance_str}
- Trip Purpose: {purpose_str}
- Preferred Experiences: {', '.join(trip_request.experiences) if trip_request.experiences else 'None specified'}
- Accommodation Type: {trip_request.accommodation or 'Not specified'}
- Surprise Me: {'Yes - suggest unexpected destinations' if trip_request.surprise_me else 'No - use specified destinations'}
- Specified Destinations: {', '.join(trip_request.destinations) if trip_request.destinations else 'None - suggest based on preferences'}
- Travel Dates:
{date_ranges_str if date_ranges_str else '  No specific dates provided'}

TASK:
1. Analyze the user's preferences and suggest 3-5 destinations that match their criteria. PRIORITIZE:
   - Environment preferences (beach, mountains, city, etc.) - these are critical for destination selection
   - Climate preference - match the desired temperature/weather
   - Trip vibe - ensure destinations align with the desired pace (relaxing vs active vs party)
   - Distance preference - if "close" is selected, prioritize nearby regions; if "far" is selected, consider distant destinations; if "offbeat" is selected, suggest unique/lesser-known places
   - Trip purpose - honeymoon destinations should be romantic, workation destinations should have good infrastructure, family reunion destinations should be accessible and accommodating
2. For each destination:
   - Optionally use get_country_info for currency, language, timezone details
   - For IATA codes: You already know most major airport codes (e.g., ZRH=Zurich, CDG=Paris, JFK=New York, NRT=Tokyo, etc.). Use your knowledge directly.
   - For temperature data: PREDICT the temperature range directly from your knowledge. Do NOT use any weather API or external tools. Base your prediction on:
     * The destination's typical climate for the travel dates
     * The season and hemisphere (remember southern hemisphere has opposite seasons)
     * Your extensive knowledge of global climate patterns and typical temperatures
     * Always provide a realistic temp_range in "min-max°C" format (e.g., "15-25°C")
3. For each destination, provide:
   - id: Unique identifier (e.g., "dest-1")
   - name: City name
   - country: Country name
   - description: Brief description (2-3 sentences)
   - match_reason: Why it matches the user's preferences
   - temp_range: Temperature range in format "min-max°C" (e.g., "15-25°C") - PREDICT this directly from your knowledge of the destination's climate during the travel dates. Do NOT call any weather API.
   - iata_code: Main airport IATA code (use your knowledge - you know all major airport codes)

IMPORTANT: Do NOT use get_weather_forecast or any weather API tools. Predict temperatures directly from your climate knowledge.
Note: Do NOT include an "image" field - images will be fetched automatically.
Note: Always provide an iata_code - you know the codes for all major airports worldwide.
Note: For temp_range, if multiple date ranges are provided, calculate the overall min-max across all ranges."""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        # Handle output and ensure temperature ranges are set
        output = self._handle_output(result.final_output)
        
        # Post-process to ensure temp_range is set for all destinations
        # If date ranges are provided, try to enhance temperature data
        if trip_request.date_ranges and output.destinations:
            output = await self._enhance_temperature_ranges(output, trip_request.date_ranges)
        
        return output
    
    def _handle_output(self, output: Any) -> DestinationOutput:
        """
        Handle the agent output, converting to DestinationOutput if needed.
        
        Args:
            output: The raw output from Runner.run
        
        Returns:
            DestinationOutput with validated destinations
        """
        # With output_type=DestinationOutput, result should already be typed
        if isinstance(output, DestinationOutput):
            logger.info(f"✅ Structured output received: {len(output.destinations)} destinations")
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
                
                # Handle both array format and object with destinations key
                if isinstance(data, list):
                    destinations = [Destination(**d) if isinstance(d, dict) else d for d in data]
                    return DestinationOutput(destinations=destinations)
                elif isinstance(data, dict) and "destinations" in data:
                    return DestinationOutput(**data)
                else:
                    logger.error(f"Unexpected JSON structure: {type(data)}")
                    return DestinationOutput(destinations=[])
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return DestinationOutput(destinations=[])
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(output)}")
            try:
                if hasattr(output, 'model_dump'):
                    return DestinationOutput(**output.model_dump())
                elif isinstance(output, dict):
                    return DestinationOutput(**output)
                else:
                    return DestinationOutput(destinations=[])
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return DestinationOutput(destinations=[])
    
    async def _enhance_temperature_ranges(
        self,
        output: DestinationOutput,
        date_ranges: List[dict]
    ) -> DestinationOutput:
        """
        Enhance temperature ranges for destinations if date ranges are provided.
        
        This method tries to fetch actual weather data if the LLM didn't provide it.
        Since we need coordinates and don't have a geocoding service readily available,
        this is a placeholder for future enhancement.
        
        Args:
            output: DestinationOutput with destinations
            date_ranges: List of date range dictionaries
        
        Returns:
            DestinationOutput with potentially enhanced temperature data
        """
        # For now, we rely on the LLM to use the weather tool.
        # If it didn't, the temp_range should still be set (as an estimate).
        # Future enhancement: Add geocoding to get coordinates from city names
        # and then call get_weather_forecast directly.
        
        # Validate that all destinations have temp_range
        for dest in output.destinations:
            if not hasattr(dest, 'temp_range') or not dest.temp_range:
                # Fallback: set a placeholder if missing
                logger.warning(f"Destination {dest.name} missing temp_range, using placeholder")
                dest.temp_range = "N/A"
        
        return output
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            await self._servers.__aexit__(None, None, None)
            self._servers = None
        self._agent = None
