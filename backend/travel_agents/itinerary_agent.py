"""
Itinerary Generation Agent

Generates day-by-day activity suggestions for a destination using:
1. Yelp API (via mcp-activities) - Real businesses with clickable URLs (for supported regions)
2. LLM knowledge - General suggestions for experiences (global fallback)

If Yelp fails (unsupported location), gracefully falls back to pure LLM suggestions.

Uses OpenAI's structured output feature (output_type) for reliable JSON responses.
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, Type

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
)
from pydantic import BaseModel

from config import Config
from .mcp_container_helper import ensure_container_running
from .base_agent import BaseAgent

# Import models after adding backend_dir to path
from models import (
    ItineraryInput,
    ItineraryOutput,
    ItineraryDay,
    ItineraryActivity,
    AgentResult,
    AgentType,
    ValidationResult,
)


class ItineraryAgent(BaseAgent):
    """
    Agent specialized in generating day-by-day itinerary suggestions.
    
    Tries Yelp API first for real business data with clickable URLs.
    Falls back to pure LLM if Yelp fails (unsupported location, API error).
    
    Uses structured output (output_type=ItineraryOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the itinerary agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
        """
        super().__init__(model=model)
        self._agent_with_yelp: Optional[Agent] = None
        self._agent_llm_only: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
    
    @property
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        return AgentType.ITINERARY
    
    def get_input_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for input validation."""
        return ItineraryInput
    
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for output validation."""
        return ItineraryOutput
    
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute itinerary generation based on input parameters.
        
        Tries Yelp first, falls back to LLM if Yelp fails.
        
        Args:
            params: Dictionary matching ItineraryInput schema
        
        Returns:
            AgentResult with generated itinerary
        """
        try:
            logger.info("=" * 60)
            logger.info("📅 ITINERARY AGENT EXECUTE (Yelp with LLM fallback)")
            logger.info("=" * 60)
            
            # Convert params to ItineraryInput for validation
            itinerary_input = ItineraryInput(**params)
            
            # Try with Yelp first, fall back to pure LLM if it fails
            try:
                logger.info("🔄 Attempting Yelp-enabled itinerary generation...")
                itinerary_output = await self._generate_with_yelp(itinerary_input)
                logger.info("✅ Yelp-enabled itinerary generated successfully!")
            except Exception as yelp_error:
                logger.warning(f"⚠️ Yelp failed: {yelp_error}")
                logger.info("🔄 Falling back to pure LLM itinerary generation...")
                itinerary_output = await self._generate_llm_only(itinerary_input)
                logger.info("✅ LLM-only itinerary generated successfully!")
            
            logger.info(f"✅ Generated itinerary with {len(itinerary_output.days)} days")
            total_activities = sum(len(day.suggested_activities) for day in itinerary_output.days)
            logger.info(f"   Total activities suggested: {total_activities}")
            
            # Count Yelp vs LLM activities
            yelp_count = sum(
                1 for day in itinerary_output.days 
                for act in day.suggested_activities 
                if act.source == "yelp"
            )
            logger.info(f"   Yelp activities: {yelp_count}, LLM suggestions: {total_activities - yelp_count}")
            
            # Convert to dict format for AgentResult
            days_data = [day.model_dump() for day in itinerary_output.days]
            
            return AgentResult(
                agent_type=self.agent_type,
                success=True,
                data={"days": days_data},
                validation=ValidationResult(is_valid=True)
            )
            
        except Exception as e:
            logger.error(f"Error in itinerary agent execution: {e}")
            import traceback
            traceback.print_exc()
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )
    
    async def _create_yelp_agent(self) -> Agent:
        """Create the agent with mcp-activities MCP server."""
        if self._agent_with_yelp is not None:
            logger.info("♻️ Reusing existing Yelp-enabled agent")
            return self._agent_with_yelp
        
        logger.info("🔧 Creating Itinerary Agent with Yelp MCP server...")
        
        # Ensure container is running
        logger.info(f"🐳 Checking container: {Config.MCP_ACTIVITIES_CONTAINER}")
        ensure_container_running(Config.MCP_ACTIVITIES_CONTAINER)
        
        # Get runtime permissions
        runtime_permissions = Config.get_runtime_permissions()
        
        # Create activities MCP manifest
        activities_manifest = DevMCPManifest(
            name="mcp-activities",
            description="MCP server for activity search via Yelp APIs",
            registry=Registry.PYPI,
            package_name="requests",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_ACTIVITIES_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True
        )
        
        # Create and start MCP servers
        self._servers = MCPServers(
            SandboxedMCPStdio(
                manifest=activities_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=120,  # Shorter timeout for faster fallback
            )
        )
        
        logger.info("⏳ Initializing MCP server...")
        await self._servers.__aenter__()
        logger.info("✅ MCP server connected!")
        
        # Create agent with MCP server
        self._agent_with_yelp = Agent(
            name="Itinerary Generation Agent (Yelp)",
            model=self.model,
            mcp_servers=self._servers,
            output_type=ItineraryOutput,
        )
        
        return self._agent_with_yelp
    
    async def _create_llm_agent(self) -> Agent:
        """Create the agent without MCP servers (pure LLM)."""
        if self._agent_llm_only is not None:
            return self._agent_llm_only
        
        logger.info("🔧 Creating pure LLM Itinerary Agent...")
        
        self._agent_llm_only = Agent(
            name="Itinerary Generation Agent (LLM)",
            model=self.model,
            mcp_servers=[],
            output_type=ItineraryOutput,
        )
        
        return self._agent_llm_only
    
    async def _generate_with_yelp(self, itinerary_input: ItineraryInput) -> ItineraryOutput:
        """Generate itinerary using Yelp MCP server."""
        agent = await self._create_yelp_agent()
        
        experiences_str = ', '.join(itinerary_input.experiences) if itinerary_input.experiences else 'No specific preferences'
        
        prompt = f"""You are a travel itinerary expert. Generate a detailed {itinerary_input.num_days}-day itinerary for {itinerary_input.destination}, {itinerary_input.country}.

USER PREFERENCES:
- Destination: {itinerary_input.destination}, {itinerary_input.country}
- Trip Duration: {itinerary_input.num_days} days
- Preferred Experiences: {experiences_str}
- Budget Range: ${itinerary_input.budget[0]:,} - ${itinerary_input.budget[1]:,}
- Traveler Type: {itinerary_input.traveler_type}
- Group Size: {itinerary_input.group_size} people

USE THE YELP MCP SERVER:
Call the search_activities tool to find real activities. Try categories like:
- "restaurants" for dining
- "attractions" for tourist spots
- "bars" for nightlife

The tool returns activities with yelp_url - use this for the 'url' field!

GENERATE A MIXED ITINERARY with 3-4 activities per day:
- id: Unique identifier
- name: Activity name  
- description: Brief 1-2 sentence description
- duration: Estimated duration
- estimated_price: Cost per person
- category: Culture, Food, Adventure, Nature, Wellness, Shopping, Entertainment
- time_of_day: morning, afternoon, evening, or full day
- url: Use yelp_url from Yelp results (null for LLM suggestions)
- source: "yelp" for Yelp results, "llm" for your suggestions

Mix Yelp activities (with clickable URLs) and LLM suggestions for variety.

For each day:
- day: Day number
- date_label: Descriptive label
- suggested_activities: 3-4 activities"""

        result = await Runner.run(agent, input=prompt)
        return self._handle_output(result.final_output)
    
    async def _generate_llm_only(self, itinerary_input: ItineraryInput) -> ItineraryOutput:
        """Generate itinerary using pure LLM (fallback)."""
        agent = await self._create_llm_agent()
        
        experiences_str = ', '.join(itinerary_input.experiences) if itinerary_input.experiences else 'No specific preferences'
        
        prompt = f"""You are a travel itinerary expert. Generate a detailed {itinerary_input.num_days}-day itinerary for {itinerary_input.destination}, {itinerary_input.country}.

USER PREFERENCES:
- Destination: {itinerary_input.destination}, {itinerary_input.country}
- Trip Duration: {itinerary_input.num_days} days
- Preferred Experiences: {experiences_str}
- Budget Range: ${itinerary_input.budget[0]:,} - ${itinerary_input.budget[1]:,}
- Traveler Type: {itinerary_input.traveler_type}
- Group Size: {itinerary_input.group_size} people

Generate a day-by-day itinerary with 3-4 activities per day:
- id: Unique identifier (e.g., "act-1a")
- name: Activity name
- description: Brief 1-2 sentence description
- duration: Estimated duration
- estimated_price: Cost per person
- category: Culture, Food, Adventure, Nature, Wellness, Shopping, Entertainment
- time_of_day: morning, afternoon, evening, or full day
- url: Set to null
- source: Set to "llm"

GUIDELINES:
1. Distribute activities across morning, afternoon, and evening
2. For Day 1, include arrival activities
3. For the last day, consider departure timing
4. Make activities specific to {itinerary_input.destination}
5. Include a mix of free and paid activities

For each day:
- day: Day number
- date_label: Descriptive label
- suggested_activities: 3-4 activities"""

        result = await Runner.run(agent, input=prompt)
        return self._handle_output(result.final_output)
    
    def _handle_output(self, output: Any) -> ItineraryOutput:
        """Handle the agent output, converting to ItineraryOutput if needed."""
        if isinstance(output, ItineraryOutput):
            logger.info(f"✅ Structured output received: {len(output.days)} days")
            return output
        elif isinstance(output, str):
            logger.warning("⚠️ Received string, attempting to parse...")
            try:
                output_str = output.strip()
                if output_str.startswith("```json"):
                    output_str = output_str[7:]
                if output_str.startswith("```"):
                    output_str = output_str[3:]
                if output_str.endswith("```"):
                    output_str = output_str[:-3]
                output_str = output_str.strip()
                
                data = json.loads(output_str)
                
                if isinstance(data, list):
                    days = [ItineraryDay(**d) if isinstance(d, dict) else d for d in data]
                    return ItineraryOutput(days=days)
                elif isinstance(data, dict) and "days" in data:
                    return ItineraryOutput(**data)
                else:
                    return ItineraryOutput(days=[])
            except Exception as e:
                logger.error(f"Failed to parse: {e}")
                return ItineraryOutput(days=[])
        else:
            logger.warning(f"⚠️ Unexpected type: {type(output)}")
            try:
                if hasattr(output, 'model_dump'):
                    return ItineraryOutput(**output.model_dump())
                elif isinstance(output, dict):
                    return ItineraryOutput(**output)
                else:
                    return ItineraryOutput(days=[])
            except Exception as e:
                logger.error(f"Failed to convert: {e}")
                return ItineraryOutput(days=[])
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            try:
                await self._servers.__aexit__(None, None, None)
            except:
                pass
            self._servers = None
        self._agent_with_yelp = None
        self._agent_llm_only = None

