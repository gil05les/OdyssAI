"""
Transport Agent (Car Rental)

Specialized agent for car rental search, pricing, and booking operations.
Uses mcp-cars MCP server to interact with Amadeus car rental APIs.

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
logger = get_agent_logger('transport')
mcp_logger = get_mcp_logger('cars')

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
    CarRentalOption,
    AgentResult,
    AgentType,
    ValidationResult,
)


class TransportAgent(BaseAgent):
    """
    Agent specialized in car rental operations.
    
    Handles car rental search, pricing, and booking queries
    using the mcp-cars MCP server.
    
    Uses structured output (output_type=TransportOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the transport agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
        """
        super().__init__(model=model)
        self._agent: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
    
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
        Execute car rental search based on input parameters.
        
        Uses structured output - the LLM returns a TransportOutput directly.
        
        Args:
            params: Dictionary matching TransportInput schema
        
        Returns:
            AgentResult with car rental search results
        """
        try:
            log_agent_input(logger, "TransportAgent", "execute", params)
            log_agent_state(logger, "TransportAgent", "EXECUTING", {"params": params})
            
            # Extract parameters
            pickup_iata = params.get("pickup_iata", "")
            pickup_date = params.get("pickup_date", "")
            dropoff_date = params.get("dropoff_date", "")
            pickup_time = params.get("pickup_time")
            dropoff_time = params.get("dropoff_time")
            
            logger.info("=" * 60)
            logger.info("🚗 TRANSPORT AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            logger.info(f"  Pickup IATA:  {pickup_iata}")
            logger.info(f"  Pickup Date:  {pickup_date}")
            logger.info(f"  Dropoff Date: {dropoff_date}")
            logger.info(f"  Pickup Time:  {pickup_time or 'Not specified'}")
            logger.info(f"  Dropoff Time: {dropoff_time or 'Not specified'}")
            logger.info("-" * 60)
            
            # Call the search method - returns structured TransportOutput
            logger.info("📡 Calling search_car_rentals (structured output)...")
            transport_output = await self.search_car_rentals(
                pickup_iata=pickup_iata,
                pickup_date=pickup_date,
                dropoff_date=dropoff_date,
                pickup_time=pickup_time,
                dropoff_time=dropoff_time
            )
            
            logger.info("-" * 60)
            logger.info(f"✅ Received {len(transport_output.car_rentals)} car rentals (structured)")
            
            for i, car in enumerate(transport_output.car_rentals[:3]):  # Log first 3
                logger.info(f"  Car {i+1}: {car.company} {car.vehicle_name} - ${car.total_price}")
            
            logger.info("=" * 60)
            
            # Convert TransportOutput to dict for AgentResult
            car_rentals_data = [car.model_dump() for car in transport_output.car_rentals]
            
            result_data = {
                "car_rentals": car_rentals_data,
                "search_summary": transport_output.search_summary
            }
            
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data=result_data,
                validation=ValidationResult(is_valid=True)
            )
            
            log_agent_output(logger, "TransportAgent", "execute", result_data, success=True)
            log_agent_state(logger, "TransportAgent", "COMPLETED", {"car_rentals_found": len(car_rentals_data)})
            
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
        """Create the agent with mcp-cars MCP server and structured output."""
        if self._agent is not None:
            logger.info("♻️  Reusing existing Transport Agent instance")
            return self._agent
        
        logger.info("🔧 Creating new Transport Agent (with structured output)...")
        
        # Ensure long-running container is running (started via Makefile)
        logger.info(f"🐳 Checking container: {Config.MCP_CARS_CONTAINER}")
        ensure_container_running(Config.MCP_CARS_CONTAINER)
        
        # Get runtime permissions
        runtime_permissions = Config.get_runtime_permissions()
        logger.info(f"🔐 Runtime permissions configured: {len(runtime_permissions)} rules")
        
        # Create cars MCP manifest
        logger.info("📦 Creating MCP cars manifest...")
        cars_manifest = DevMCPManifest(
            name="mcp-cars",
            description="MCP server for car rental search, pricing, and booking via Amadeus APIs",
            registry=Registry.PYPI,
            package_name="amadeus",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_CARS_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True
        )
        
        # Create and start MCP servers (use long-running containers)
        logger.info("🚀 Starting MCP server connection...")
        self._servers = MCPServers(
            SandboxedMCPStdio(
                manifest=cars_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=300,
            )
        )
        
        logger.info("⏳ Initializing MCP server (this may take a moment)...")
        await self._servers.__aenter__()
        logger.info("✅ MCP server connected!")
        
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
    
    async def search_car_rentals(
        self,
        pickup_iata: str,
        pickup_date: str,
        dropoff_date: str,
        pickup_time: Optional[str] = None,
        dropoff_time: Optional[str] = None
    ) -> TransportOutput:
        """
        Search for car rentals at an airport.
        
        Uses structured output - returns TransportOutput directly.
        
        Args:
            pickup_iata: IATA code of the pickup airport (e.g., "LIS")
            pickup_date: Pickup date in YYYY-MM-DD format
            dropoff_date: Dropoff date in YYYY-MM-DD format
            pickup_time: Optional pickup time (HH:MM format)
            dropoff_time: Optional dropoff time (HH:MM format)
        
        Returns:
            TransportOutput with structured car rental data
        """
        import time
        start_time = time.time()
        
        log_agent_state(logger, "TransportAgent", "SEARCHING_CAR_RENTALS", {
            "pickup_iata": pickup_iata,
            "pickup_date": pickup_date,
            "dropoff_date": dropoff_date,
            "pickup_time": pickup_time,
            "dropoff_time": dropoff_time
        })
        
        logger.info("🔄 search_car_rentals() called")
        logger.debug(f"Creating agent instance...")
        agent = await self._create_agent()
        logger.debug(f"Agent instance created")
        
        prompt = f"""Search for car rentals at {pickup_iata} airport.

Search Parameters:
- Pickup Date: {pickup_date}
- Dropoff Date: {dropoff_date}
"""
        
        if pickup_time:
            prompt += f"- Pickup Time: {pickup_time}\n"
        
        if dropoff_time:
            prompt += f"- Dropoff Time: {dropoff_time}\n"
        
        prompt += """
Instructions:
1. Use the search_cars_at_airport tool to find available vehicles
2. The tool returns a response with a "car_offers" array. Each offer has these fields:
   - offer_id: Unique identifier for the offer
   - provider: Rental company name
   - vehicle: Object with category, make, model, transmission, airConditioning, fuel, seats, doors
   - pricing: Object with total, currency, base, taxes
   - pickup_location: Location information
   - dropoff_location: Location information
3. Extract the car rental information and return it in the structured TransportOutput format
4. For each car offer, map the fields as follows:
   - id: Use the offer_id from the API response
   - company: Use provider from the API response
   - vehicle_type: Use vehicle.category from the API response (e.g., "ECONOMY", "COMPACT", "SUV", "LUXURY")
   - vehicle_name: Combine vehicle.make and vehicle.model (e.g., "Toyota Corolla" or just model if make is not available)
   - price_per_day: Calculate from pricing.total divided by number of days between pickup and dropoff dates
   - total_price: Use pricing.total from the API response as a number (float)
   - currency: Use pricing.currency from the API response (e.g., "CHF", "EUR")
   - features: Build from vehicle properties:
     * Include "Automatic" if transmission is "AUTOMATIC"
     * Include "Manual" if transmission is "MANUAL"
     * Include "Air Conditioning" if airConditioning is true
     * Include fuel type (e.g., "Diesel", "Petrol", "Electric") if available
     * Include "GPS" if mentioned in the offer (may not always be available)
5. Include at least the top 5 best options that match the criteria
6. Provide a brief search_summary describing what was found, including the airport, number of cars found, and price range

IMPORTANT: You must call the search_cars_at_airport tool with the exact parameters provided above. The tool requires pickup_iata, pickup_date, and dropoff_date parameters.
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
            logger.info(f"✅ Structured output received: {len(result.final_output.car_rentals)} car rentals")
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
                return TransportOutput(car_rentals=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(result.final_output)}")
            try:
                if hasattr(result.final_output, 'model_dump'):
                    return TransportOutput(**result.final_output.model_dump())
                elif isinstance(result.final_output, dict):
                    return TransportOutput(**result.final_output)
                else:
                    return TransportOutput(car_rentals=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return TransportOutput(car_rentals=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def handle_transport_query(self, query: str) -> TransportOutput:
        """
        Handle a general transport/car rental-related query.
        
        Args:
            query: User's transport-related query
        
        Returns:
            TransportOutput with structured response
        """
        agent = await self._create_agent()
        
        prompt = f"""You are a car rental and transportation assistant. Help the user with their transportation request.

User Query: {query}

Instructions:
1. Use the available car rental tools to search for cars:
   - search_cars_at_airport: For searching by airport IATA code (e.g., "LIS", "BCN", "ZRH")
   - get_car_offer_details: For getting details about a specific offer
2. If the user mentions an airport name, you may need to convert it to an IATA code first
3. Extract car rental information from the tool responses and return it in the structured TransportOutput format
4. For each car rental, provide:
   - id: The offer_id from the API response
   - company: The provider from the API response
   - vehicle_type: Use vehicle.category (e.g., "ECONOMY", "COMPACT", "SUV", "LUXURY")
   - vehicle_name: Combine vehicle.make and vehicle.model
   - price_per_day: Calculate from pricing.total divided by number of days
   - total_price: Use pricing.total as a number
   - currency: Use pricing.currency from response
   - features: Build from vehicle properties (transmission, airConditioning, fuel type)
5. Include at least the top 5 best options
6. Provide a brief search_summary describing what was found

IMPORTANT: You must call one of the search tools (search_cars_at_airport) to get car rental data. The tool responses will have a "car_offers" array with the car rental information."""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        # Handle structured output
        if isinstance(result.final_output, TransportOutput):
            return result.final_output
        else:
            return self._handle_output(result.final_output)
    
    def _handle_output(self, output: Any) -> TransportOutput:
        """
        Handle the agent output, converting to TransportOutput if needed.
        
        Args:
            output: The raw output from Runner.run
        
        Returns:
            TransportOutput with validated car rentals
        """
        # With output_type=TransportOutput, result should already be typed
        if isinstance(output, TransportOutput):
            logger.info(f"✅ Structured output received: {len(output.car_rentals)} car rentals")
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
                return TransportOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return TransportOutput(car_rentals=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(output)}")
            try:
                if hasattr(output, 'model_dump'):
                    return TransportOutput(**output.model_dump())
                elif isinstance(output, dict):
                    return TransportOutput(**output)
                else:
                    return TransportOutput(car_rentals=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return TransportOutput(car_rentals=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            await self._servers.__aexit__(None, None, None)
            self._servers = None
        self._agent = None
