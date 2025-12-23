"""
Activities Agent

Specialized agent for activity/business search operations.
Uses mcp-activities MCP server to interact with Yelp APIs.

This agent can suggest activities from both:
1. Yelp API (via MCP server) - Real businesses with URLs
2. LLM knowledge - General suggestions based on context

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
logger = get_agent_logger('activities')
mcp_logger = get_mcp_logger('activities')

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
    ActivitiesInput,
    ActivitiesOutput,
    ActivityOption,
    AgentResult,
    AgentType,
    ValidationResult,
)


class ActivitiesAgent(BaseAgent):
    """
    Agent specialized in activity/business search operations.
    
    Handles activity search using Yelp API (restaurants, attractions, museums, etc.)
    while also allowing LLM to suggest activities from its own knowledge.
    
    Uses structured output (output_type=ActivitiesOutput) for reliable parsing.
    
    Extends BaseAgent to support the pluggable orchestrator architecture.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the activities agent.
        
        Args:
            model: Model to use (defaults to Config.DEFAULT_MODEL)
        """
        super().__init__(model=model)
        self._agent: Optional[Agent] = None
        self._servers: Optional[MCPServers] = None
    
    @property
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        return AgentType.ACTIVITIES
    
    def get_input_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for input validation."""
        return ActivitiesInput
    
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic model for output validation."""
        return ActivitiesOutput
    
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute activity search based on input parameters.
        
        Uses structured output - the LLM returns an ActivitiesOutput directly.
        
        Args:
            params: Dictionary matching ActivitiesInput schema
        
        Returns:
            AgentResult with activity search results
        """
        try:
            log_agent_input(logger, "ActivitiesAgent", "execute", params)
            log_agent_state(logger, "ActivitiesAgent", "EXECUTING", {"params": params})
            
            # Extract parameters
            location = params.get("location", "")
            category = params.get("category", "attractions")
            limit = params.get("limit", 10)
            experiences = params.get("experiences", [])
            
            logger.info("=" * 60)
            logger.info("🎯 ACTIVITIES AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            logger.info(f"  Location:    {location}")
            logger.info(f"  Category:    {category}")
            logger.info(f"  Limit:       {limit}")
            logger.info(f"  Experiences: {experiences}")
            logger.info("-" * 60)
            
            # Call the search method - returns structured ActivitiesOutput
            logger.info("📡 Calling search_activities (structured output)...")
            activities_output = await self.search_activities(
                location=location,
                category=category,
                limit=limit,
                experiences=experiences
            )
            
            logger.info("-" * 60)
            logger.info(f"✅ Received {len(activities_output.activities)} activities (structured)")
            
            for i, activity in enumerate(activities_output.activities[:3]):  # Log first 3
                source_icon = "🔗" if activity.source == "yelp" else "💡"
                logger.info(f"  Activity {i+1}: {source_icon} {activity.name} ({activity.source})")
            
            logger.info("=" * 60)
            
            # Convert ActivitiesOutput to dict for AgentResult
            activities_data = [activity.model_dump() for activity in activities_output.activities]
            
            result_data = {
                "activities": activities_data,
                "search_summary": activities_output.search_summary
            }
            
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data=result_data,
                validation=ValidationResult(is_valid=True)
            )
            
            log_agent_output(logger, "ActivitiesAgent", "execute", result_data, success=True)
            log_agent_state(logger, "ActivitiesAgent", "COMPLETED", {"activities_found": len(activities_data)})
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in activities agent execution: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback:\n{error_trace}")
            
            error_result = AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )
            
            log_agent_output(logger, "ActivitiesAgent", "execute", {"error": str(e)}, success=False)
            log_agent_state(logger, "ActivitiesAgent", "FAILED", {"error": str(e)})
            
            return error_result
    
    async def _create_agent(self) -> Agent:
        """Create the agent with mcp-activities MCP server and structured output."""
        if self._agent is not None:
            logger.info("♻️  Reusing existing Activities Agent instance")
            return self._agent
        
        logger.info("🔧 Creating new Activities Agent (with structured output)...")
        
        # Ensure long-running container is running (started via Makefile)
        logger.info(f"🐳 Checking container: {Config.MCP_ACTIVITIES_CONTAINER}")
        ensure_container_running(Config.MCP_ACTIVITIES_CONTAINER)
        
        # Get runtime permissions
        runtime_permissions = Config.get_runtime_permissions()
        logger.info(f"🔐 Runtime permissions configured: {len(runtime_permissions)} rules")
        
        # Create activities MCP manifest
        logger.info("📦 Creating MCP activities manifest...")
        activities_manifest = DevMCPManifest(
            name="mcp-activities",
            description="MCP server for activity search via Yelp APIs - restaurants, attractions, museums, etc.",
            registry=Registry.PYPI,
            package_name="requests",
            permissions=[
                Permission.MCP_AC_NETWORK_CLIENT,
                Permission.MCP_AC_SYSTEM_ENV_READ,
            ],
            code_mount=Config.MCP_ACTIVITIES_PATH,
            exec_command="bash /sandbox/start.sh",
            preinstalled=True  # Use pre-installed dependencies
        )
        
        # Create and start MCP servers (use long-running containers)
        logger.info("🚀 Starting MCP server connection...")
        self._servers = MCPServers(
            SandboxedMCPStdio(
                manifest=activities_manifest,
                runtime_permissions=runtime_permissions,
                remove_container_after_run=False,
                client_session_timeout_seconds=300,
            )
        )
        
        logger.info("⏳ Initializing MCP server (this may take a moment)...")
        await self._servers.__aenter__()
        logger.info("✅ MCP server connected!")
        
        logger.info(f"🤖 Creating LLM agent with model: {self.model}")
        logger.info("📋 Using structured output: ActivitiesOutput")
        
        # Create agent WITH structured output_type
        self._agent = Agent(
            name="Activities Agent",
            model=self.model,
            mcp_servers=self._servers,
            output_type=ActivitiesOutput,  # Structured output - LLM returns typed JSON
        )
        
        logger.info("✅ Activities Agent ready!")
        return self._agent
    
    async def search_activities(
        self,
        location: str,
        category: str = "attractions",
        limit: int = 10,
        experiences: List[str] = None
    ) -> ActivitiesOutput:
        """
        Search for activities in a specific location.
        
        Uses both Yelp API (via MCP) and LLM knowledge for suggestions.
        
        Args:
            location: City/location (e.g., "St. Gallen, Switzerland")
            category: Category (attractions, restaurants, museums, etc.)
            limit: Number of results to return
            experiences: User's interests/preferences
        
        Returns:
            ActivitiesOutput with structured activity data
        """
        import time
        start_time = time.time()
        
        experiences = experiences or []
        
        log_agent_state(logger, "ActivitiesAgent", "SEARCHING_ACTIVITIES", {
            "location": location,
            "category": category,
            "limit": limit,
            "experiences": experiences
        })
        
        logger.info("🔄 search_activities() called")
        logger.debug(f"Creating agent instance...")
        agent = await self._create_agent()
        logger.debug(f"Agent instance created")
        
        # Build prompt that encourages both Yelp and LLM suggestions
        prompt = f"""Search for activities in {location}.

Search Parameters:
- Category: {category}
- Number of results: {limit}
"""
        
        if experiences:
            prompt += f"- User interests: {', '.join(experiences)}\n"
        
        prompt += """
Instructions:
1. Use the search_activities tool to find real businesses from Yelp
2. The tool returns activities with these fields:
   - id: Unique identifier
   - name: Business name
   - rating: Rating (if available)
   - review_count: Number of reviews
   - price: Price level (e.g., "$$")
   - address: Full address
   - yelp_url: Clickable link to Yelp page (IMPORTANT: include this!)
   - categories: List of category names
   - image_url: Image URL
   - source: "yelp" (indicates data is from Yelp)

3. Map the Yelp results to the ActivitiesOutput format:
   - id: Use the id from Yelp
   - name: Use the name from Yelp
   - description: Create a brief description based on categories and location
   - category: Use the primary category
   - rating: Use rating if available
   - review_count: Use review_count
   - price: Use price level
   - address: Use address
   - image_url: Use image_url
   - url: Use yelp_url - THIS IS THE CLICKABLE LINK TO YELP
   - source: Set to "yelp" for Yelp results
   - phone, latitude, longitude: Include if available

4. You may ALSO suggest additional activities from your own knowledge that aren't in Yelp results.
   For these, set source to "llm" and provide a good description.
   These suggestions are valuable for unique local experiences.

5. Return a mix of Yelp results AND your own suggestions for variety.
   Prioritize Yelp results for businesses (restaurants, cafes, shops).
   Add LLM suggestions for unique experiences, viewpoints, walking routes, etc.

6. Provide a brief search_summary describing what was found.

IMPORTANT: Always include the Yelp URL in the 'url' field so users can click through to see more details!
"""

        logger.info("📤 Sending prompt to LLM (structured output mode)...")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.debug(f"Full prompt:\n{prompt}")
        
        log_agent_state(logger, "ActivitiesAgent", "CALLING_LLM", {
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
        
        # With output_type=ActivitiesOutput, result.final_output is already the typed object
        if isinstance(result.final_output, ActivitiesOutput):
            logger.info(f"✅ Structured output received: {len(result.final_output.activities)} activities")
            return result.final_output
        elif isinstance(result.final_output, str):
            # Fallback: try to parse as JSON if string returned
            logger.warning("⚠️ Received string instead of structured output, attempting to parse...")
            try:
                output_str = result.final_output.strip()
                if output_str.startswith("```json"):
                    output_str = output_str[7:]
                if output_str.startswith("```"):
                    output_str = output_str[3:]
                if output_str.endswith("```"):
                    output_str = output_str[:-3]
                output_str = output_str.strip()
                
                data = json.loads(output_str)
                return ActivitiesOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return ActivitiesOutput(activities=[], search_summary=f"Failed to parse response: {str(e)}")
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(result.final_output)}")
            try:
                if hasattr(result.final_output, 'model_dump'):
                    return ActivitiesOutput(**result.final_output.model_dump())
                elif isinstance(result.final_output, dict):
                    return ActivitiesOutput(**result.final_output)
                else:
                    return ActivitiesOutput(activities=[], search_summary="Unexpected response format")
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return ActivitiesOutput(activities=[], search_summary=f"Failed to convert response: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._servers is not None:
            await self._servers.__aexit__(None, None, None)
            self._servers = None
        self._agent = None

