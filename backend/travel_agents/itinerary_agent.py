"""
Itinerary Generation Agent

Generates day-by-day activity suggestions for a destination using LLM reasoning.
No MCP servers - uses pure LLM knowledge to suggest activities based on:
- Destination and country
- User experience preferences
- Budget constraints
- Trip duration
- Traveler type and group size

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
from pydantic import BaseModel

from config import Config
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
    
    Uses LLM reasoning to suggest activities for each day of the trip.
    No MCP servers - relies on LLM knowledge of destinations and activities.
    
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
        self._agent: Optional[Agent] = None
    
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
        
        Uses structured output - the LLM returns an ItineraryOutput directly.
        
        Args:
            params: Dictionary matching ItineraryInput schema
        
        Returns:
            AgentResult with generated itinerary
        """
        try:
            logger.info("=" * 60)
            logger.info("📅 ITINERARY AGENT EXECUTE (Structured Output)")
            logger.info("=" * 60)
            
            # Convert params to ItineraryInput for validation
            itinerary_input = ItineraryInput(**params)
            
            # Call the structured generation method
            itinerary_output = await self.generate_itinerary_structured(itinerary_input)
            
            logger.info(f"✅ Generated itinerary with {len(itinerary_output.days)} days")
            total_activities = sum(len(day.suggested_activities) for day in itinerary_output.days)
            logger.info(f"   Total activities suggested: {total_activities}")
            
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
    
    async def _create_agent(self) -> Agent:
        """Create the agent with structured output (no MCP servers)."""
        if self._agent is not None:
            return self._agent
        
        logger.info("Creating itinerary agent with structured output (no MCP servers)...")
        
        logger.info("📋 Using structured output: ItineraryOutput")
        
        # Create agent WITH structured output_type, NO MCP servers
        self._agent = Agent(
            name="Itinerary Generation Agent",
            model=self.model,
            mcp_servers=[],  # No MCP servers - pure LLM (empty list instead of None)
            output_type=ItineraryOutput,  # Structured output - LLM returns typed JSON
        )
        
        return self._agent
    
    async def generate_itinerary_structured(
        self,
        itinerary_input: ItineraryInput
    ) -> ItineraryOutput:
        """
        Generate itinerary based on structured input and return typed results.
        
        Uses structured output - returns ItineraryOutput directly.
        
        Args:
            itinerary_input: Structured itinerary input with all parameters
        
        Returns:
            ItineraryOutput with day-by-day activity suggestions
        """
        agent = await self._create_agent()
        
        # Build comprehensive prompt with all user preferences
        experiences_str = ', '.join(itinerary_input.experiences) if itinerary_input.experiences else 'No specific preferences'
        
        prompt = f"""You are a travel itinerary expert. Generate a detailed {itinerary_input.num_days}-day itinerary for {itinerary_input.destination}, {itinerary_input.country}.

USER PREFERENCES:
- Destination: {itinerary_input.destination}, {itinerary_input.country}
- Trip Duration: {itinerary_input.num_days} days
- Preferred Experiences: {experiences_str}
- Budget Range: ${itinerary_input.budget[0]:,} - ${itinerary_input.budget[1]:,} (total for all activities)
- Traveler Type: {itinerary_input.traveler_type}
- Group Size: {itinerary_input.group_size} people

TASK:
Generate a day-by-day itinerary with 3-4 activity suggestions per day. For each activity, provide:
- id: Unique identifier (e.g., "act-1a", "act-1b", "act-2a")
- name: Activity name (e.g., "Sunset Wine Tasting", "Ancient Temple Tour")
- description: Brief 1-2 sentence description of the activity
- duration: Estimated duration (e.g., "2 hours", "3-4 hours", "Full day")
- estimated_price: Estimated cost per person (or total if group activity)
- category: Activity category (e.g., "Culture", "Food", "Adventure", "Nature", "Wellness", "Shopping", "Entertainment")
- time_of_day: When it typically occurs ("morning", "afternoon", "evening", or "full day")

GUIDELINES:
1. Distribute activities across morning, afternoon, and evening for each day
2. Mix activity types based on user experience preferences
3. Ensure total estimated prices stay within budget range
4. Consider traveler type (solo travelers might prefer different activities than families)
5. For Day 1, include arrival/check-in activities
6. For the last day, consider departure timing
7. Make activities realistic and specific to {itinerary_input.destination}
8. Include a mix of free/low-cost and paid activities
9. Consider local culture, cuisine, and must-see attractions

For each day, provide:
- day: Day number (1, 2, 3, etc.)
- date_label: Descriptive label (e.g., "Day 1 - Arrival & Exploration", "Day 2 - Cultural Immersion")
- suggested_activities: List of 3-4 activities for that day

Generate activities that showcase what's cool and unique about {itinerary_input.destination} based on your knowledge of the destination."""

        result = await Runner.run(
            agent,
            input=prompt,
        )
        
        # Handle output and ensure it's properly formatted
        output = self._handle_output(result.final_output)
        
        return output
    
    def _handle_output(self, output: Any) -> ItineraryOutput:
        """
        Handle the agent output, converting to ItineraryOutput if needed.
        
        Args:
            output: The raw output from Runner.run
        
        Returns:
            ItineraryOutput with validated itinerary days
        """
        # With output_type=ItineraryOutput, result should already be typed
        if isinstance(output, ItineraryOutput):
            logger.info(f"✅ Structured output received: {len(output.days)} days")
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
                
                # Handle both array format and object with days key
                if isinstance(data, list):
                    days = [ItineraryDay(**d) if isinstance(d, dict) else d for d in data]
                    return ItineraryOutput(days=days)
                elif isinstance(data, dict) and "days" in data:
                    return ItineraryOutput(**data)
                else:
                    logger.error(f"Unexpected JSON structure: {type(data)}")
                    return ItineraryOutput(days=[])
            except Exception as e:
                logger.error(f"Failed to parse string response: {e}")
                return ItineraryOutput(days=[])
        else:
            # Unknown type - try to convert
            logger.warning(f"⚠️ Unexpected output type: {type(output)}")
            try:
                if hasattr(output, 'model_dump'):
                    return ItineraryOutput(**output.model_dump())
                elif isinstance(output, dict):
                    return ItineraryOutput(**output)
                else:
                    return ItineraryOutput(days=[])
            except Exception as e:
                logger.error(f"Failed to convert output: {e}")
                return ItineraryOutput(days=[])
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._agent = None

