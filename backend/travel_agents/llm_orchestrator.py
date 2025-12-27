"""
LLM Orchestrator

Main coordinator that manages the workflow between specialized agents using
LLM-based reasoning for input validation, agent routing, and output validation.

All agents now use OpenAI's structured output feature (output_type) which guarantees
that LLM responses conform to Pydantic schemas. This eliminates the need for regex
parsing and provides reliable, validated JSON responses.

Replaces the keyword-based orchestrator with intelligent LLM-driven coordination.
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(backend_dir, '..', 'python-mcp-sandbox-openai-sdk-main', 'src'))
sys.path.insert(0, backend_dir)

from agents import Agent, Runner

from config import Config
from .base_agent import BaseAgent
from .agent_registry import AgentRegistry, get_agent

from models import (
    TripRequest,
    Destination,
    AgentType,
    AgentResult,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    WorkflowResponse,
    DestinationInput,
    DestinationOutput,
    FlightOutput,
    HotelOutput,
    TransportOutput,
)

# Configure logging
logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    LLM-powered orchestrator that coordinates multiple specialized agents.
    
    All agents use structured output (output_type parameter) which means:
    - LLM responses are guaranteed to match the schema
    - No regex or manual JSON parsing needed
    - Validation happens at the SDK level
    - If LLM returns invalid data, SDK raises a clear error (can be retried)
    
    Uses LLM reasoning to:
    - Validate inputs against agent-specific schemas
    - Decide which agents to invoke (and in what order)
    - Route requests to appropriate agents
    - Aggregate results from multiple agents
    
    Supports pluggable agents via the AgentRegistry.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the LLM orchestrator.
        
        Args:
            model: LLM model to use (defaults to Config.DEFAULT_MODEL)
        """
        self.model = model or Config.DEFAULT_MODEL
        self._active_agents: Dict[str, BaseAgent] = {}
        logger.info(f"🎯 LLMOrchestrator initialized with model: {self.model}")
        logger.info("📋 All agents use structured output for reliable JSON responses")
    
    async def execute_workflow(
        self,
        request: TripRequest,
        agents_to_invoke: List[str] = None
    ) -> WorkflowResponse:
        """
        Execute the orchestration workflow.
        
        All invoked agents use structured output (output_type), guaranteeing
        properly formatted responses that match their Pydantic schemas.
        
        Args:
            request: TripRequest from frontend
            agents_to_invoke: List of agent names to invoke (default: ["destination"])
        
        Returns:
            WorkflowResponse with results from all agents
        """
        if agents_to_invoke is None:
            agents_to_invoke = ["destination"]
        
        logger.info("=" * 60)
        logger.info("🎯 ORCHESTRATOR WORKFLOW (Structured Output)")
        logger.info("=" * 60)
        logger.info(f"  Agents to invoke: {agents_to_invoke}")
        logger.info("-" * 60)
        
        # Step 1: Validate input
        logger.info("📝 Step 1: Validating input request...")
        input_validation = self._validate_trip_request(request)
        if not input_validation.is_valid:
            logger.warning(f"❌ Input validation failed: {input_validation.errors}")
            return WorkflowResponse(
                success=False,
                input_validation=input_validation,
                errors=input_validation.errors
            )
        
        logger.info("✅ Input validation passed")
        
        # Step 2: Execute each agent with structured output
        logger.info(f"🚀 Step 2: Executing {len(agents_to_invoke)} agent(s)...")
        results: Dict[str, AgentResult] = {}
        errors: List[str] = []
        
        for agent_name in agents_to_invoke:
            logger.info(f"  → Invoking {agent_name} agent (structured output)...")
            
            try:
                result = await self._execute_agent(agent_name, request)
                results[agent_name] = result
                
                if not result.success:
                    errors.append(f"{agent_name} agent failed: {result.error}")
                    logger.warning(f"  ⚠️ {agent_name} agent failed: {result.error}")
                else:
                    # Log structured output info
                    if result.data:
                        data_keys = list(result.data.keys())
                        item_counts = {k: len(v) if isinstance(v, list) else 1 for k, v in result.data.items() if not k.endswith('_summary')}
                        logger.info(f"  ✅ {agent_name} agent completed: {item_counts}")
                    else:
                        logger.info(f"  ✅ {agent_name} agent completed successfully")
                    
            except Exception as e:
                logger.error(f"  ❌ Error executing {agent_name} agent: {e}")
                import traceback
                traceback.print_exc()
                
                results[agent_name] = AgentResult(
                    agent_type=AgentType(agent_name) if agent_name in [t.value for t in AgentType] else AgentType.DESTINATION,
                    success=False,
                    error=str(e)
                )
                errors.append(f"{agent_name} agent error: {str(e)}")
        
        # Step 3: Determine overall success
        success = any(r.success for r in results.values()) if results else False
        
        logger.info("-" * 60)
        logger.info(f"📊 Workflow result: {'✅ Success' if success else '❌ Failed'}")
        logger.info("=" * 60)
        
        return WorkflowResponse(
            success=success,
            results=results,
            input_validation=input_validation,
            errors=errors
        )
    
    def _validate_trip_request(self, request: TripRequest) -> ValidationResult:
        """
        Validate the TripRequest from frontend.
        
        Performs comprehensive validation including:
        - Required fields
        - Date validity
        - Budget reasonableness
        - Group size consistency
        
        Args:
            request: TripRequest to validate
        
        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []
        
        # Validate origin
        if not request.origin or len(request.origin.strip()) == 0:
            issues.append(ValidationIssue(
                field="origin",
                message="Origin is required",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validate dates
        if request.date_ranges:
            for i, date_range in enumerate(request.date_ranges):
                try:
                    from_date = date_range.get("from")
                    to_date = date_range.get("to")
                    
                    if from_date:
                        from_parsed = datetime.strptime(from_date, "%Y-%m-%d").date()
                        # Warn if date is in the past
                        if from_parsed < date.today():
                            issues.append(ValidationIssue(
                                field=f"date_ranges[{i}].from",
                                message=f"Start date {from_date} is in the past",
                                severity=ValidationSeverity.WARNING
                            ))
                    
                    if to_date:
                        to_parsed = datetime.strptime(to_date, "%Y-%m-%d").date()
                        if from_date:
                            from_parsed = datetime.strptime(from_date, "%Y-%m-%d").date()
                            if to_parsed < from_parsed:
                                issues.append(ValidationIssue(
                                    field=f"date_ranges[{i}].to",
                                    message="End date cannot be before start date",
                                    severity=ValidationSeverity.ERROR
                                ))
                except ValueError as e:
                    issues.append(ValidationIssue(
                        field=f"date_ranges[{i}]",
                        message=f"Invalid date format: {str(e)}",
                        severity=ValidationSeverity.ERROR
                    ))
        
        # Validate budget
        if request.budget:
            min_budget, max_budget = request.budget
            if min_budget < 0:
                issues.append(ValidationIssue(
                    field="budget",
                    message="Minimum budget cannot be negative",
                    severity=ValidationSeverity.ERROR
                ))
            if max_budget < min_budget:
                issues.append(ValidationIssue(
                    field="budget",
                    message="Maximum budget must be greater than minimum",
                    severity=ValidationSeverity.ERROR
                ))
            if max_budget > 1000000:
                issues.append(ValidationIssue(
                    field="budget",
                    message="Budget seems unusually high",
                    severity=ValidationSeverity.WARNING
                ))
        
        # Validate duration
        if request.duration:
            min_days, max_days = request.duration
            if min_days < 1:
                issues.append(ValidationIssue(
                    field="duration",
                    message="Minimum duration must be at least 1 day",
                    severity=ValidationSeverity.ERROR
                ))
            if max_days < min_days:
                issues.append(ValidationIssue(
                    field="duration",
                    message="Maximum duration must be greater than minimum",
                    severity=ValidationSeverity.ERROR
                ))
            if max_days > 365:
                issues.append(ValidationIssue(
                    field="duration",
                    message="Duration exceeds one year",
                    severity=ValidationSeverity.WARNING
                ))
        
        # Validate group size
        if request.group_size < 1:
            issues.append(ValidationIssue(
                field="group_size",
                message="Group size must be at least 1",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validate traveler type consistency
        traveler_group_rules = {
            "solo": (1, 1),
            "couple": (2, 2),
            "family": (2, 20),
            "group": (3, 100),
        }
        
        if request.traveler_type in traveler_group_rules:
            min_size, max_size = traveler_group_rules[request.traveler_type]
            if not (min_size <= request.group_size <= max_size):
                issues.append(ValidationIssue(
                    field="group_size",
                    message=f"Group size {request.group_size} seems inconsistent with traveler type '{request.traveler_type}'",
                    severity=ValidationSeverity.WARNING
                ))
        
        # Validate destinations if not surprise_me
        if not request.surprise_me and not request.destinations:
            issues.append(ValidationIssue(
                field="destinations",
                message="Either enable 'surprise_me' or provide specific destinations",
                severity=ValidationSeverity.WARNING
            ))
        
        # Determine if validation passed (no ERROR-level issues)
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=not has_errors,
            issues=issues
        )
    
    async def _execute_agent(
        self,
        agent_name: str,
        request: TripRequest,
        max_retries: int = 2
    ) -> AgentResult:
        """
        Execute a specific agent with structured output, validation, and retry logic.
        
        Each agent uses output_type for structured responses, which means:
        - The LLM is instructed to return JSON matching the schema
        - The SDK validates the response automatically
        - Invalid responses can trigger retries
        
        Args:
            agent_name: Name of the agent to execute
            request: TripRequest with user preferences
            max_retries: Maximum retry attempts on failure
        
        Returns:
            AgentResult from the agent (with validated, structured data)
        """
        # Get or create agent instance
        agent = await self._get_agent(agent_name)
        if agent is None:
            return AgentResult(
                agent_type=AgentType.DESTINATION,  # Default
                success=False,
                error=f"Agent '{agent_name}' not found in registry"
            )
        
        # Convert TripRequest to agent-specific input
        agent_input = self._convert_to_agent_input(agent_name, request)
        
        # Execute with validation (uses BaseAgent's execute_with_validation)
        # The agent's execute() method returns structured output
        result = await agent.execute_with_validation(agent_input, max_retries=max_retries)
        
        return result
    
    def _convert_to_agent_input(self, agent_name: str, request: TripRequest) -> Dict[str, Any]:
        """
        Convert TripRequest to agent-specific input format.
        
        Each agent expects a specific input schema. This method extracts
        and transforms the relevant fields from the TripRequest.
        
        Args:
            agent_name: Name of the target agent
            request: TripRequest to convert
        
        Returns:
            Dictionary matching the agent's input schema
        """
        if agent_name == "destination":
            return {
                "origin": request.origin,
                "destinations": request.destinations,
                "surprise_me": request.surprise_me,
                "experiences": request.experiences,
                "budget": request.budget,
                "duration": request.duration,
                "traveler_type": request.traveler_type,
                "group_size": request.group_size,
                "date_ranges": request.date_ranges,
                "accommodation": request.accommodation,
                "environments": request.environments,
                "climate": request.climate,
                "trip_vibe": request.trip_vibe,
                "distance_preference": request.distance_preference,
                "trip_purpose": request.trip_purpose,
            }
        
        elif agent_name == "flight":
            # Extract flight-specific info
            # For flights, we need origin/destination IATA codes and dates
            departure_date = None
            return_date = None
            if request.date_ranges:
                departure_date = request.date_ranges[0].get("from")
                return_date = request.date_ranges[0].get("to")
            
            return {
                "origin": request.origin,
                "destination": request.destinations[0] if request.destinations else "",
                "departure_date": departure_date or "",
                "return_date": return_date,
                "adults": request.group_size,
                "max_price": float(request.budget[1]) if request.budget else None,
            }
        
        elif agent_name == "hotel":
            # Extract hotel-specific info
            check_in = None
            check_out = None
            if request.date_ranges:
                check_in = request.date_ranges[0].get("from")
                check_out = request.date_ranges[0].get("to")
            
            return {
                "city_code": request.destinations[0] if request.destinations else "",
                "check_in": check_in or "",
                "check_out": check_out or "",
                "guests": request.group_size,
            }
        
        elif agent_name == "transport":
            # Extract comprehensive trip context for transport
            departure_date = None
            return_date = None
            if request.date_ranges:
                departure_date = request.date_ranges[0].get("from")
                return_date = request.date_ranges[0].get("to")
            
            # Get destination info (will be populated from previous agent results)
            destination = request.destinations[0] if request.destinations else ""
            
            return {
                "destination_city": destination,  # Will be refined by destination agent results
                "destination_country": "",  # From destination agent results
                "hotel_address": "",  # From hotel selection
                "airport_code": "",  # From destination IATA code
                "itinerary_locations": [],  # From itinerary agent results
                "arrival_datetime": departure_date or "",
                "departure_datetime": return_date or "",
                "group_size": request.group_size,
            }
        
        # Default: pass through as-is
        return request.model_dump()
    
    async def _get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get or create an agent instance.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Agent instance or None if not found
        """
        if agent_name not in self._active_agents:
            agent = get_agent(agent_name, model=self.model)
            if agent:
                self._active_agents[agent_name] = agent
        
        return self._active_agents.get(agent_name)
    
    async def discover_destinations_structured(
        self,
        trip_request: TripRequest
    ) -> List[Destination]:
        """
        Discover destinations using the destination agent.
        
        This method provides backward compatibility with the old orchestrator API.
        The destination agent uses structured output (DestinationOutput) for
        reliable, validated JSON responses.
        
        Args:
            trip_request: TripRequest from frontend
        
        Returns:
            List of Destination objects
        """
        # Execute workflow with just the destination agent
        response = await self.execute_workflow(
            request=trip_request,
            agents_to_invoke=["destination"]
        )
        
        # Extract destinations from response
        return response.get_destinations()
    
    async def cleanup(self) -> None:
        """Clean up all active agent resources."""
        logger.info("🧹 Cleaning up orchestrator resources...")
        for agent_name, agent in self._active_agents.items():
            try:
                await agent.cleanup()
                logger.info(f"  ✅ Cleaned up {agent_name} agent")
            except Exception as e:
                logger.error(f"  ❌ Error cleaning up {agent_name} agent: {e}")
        
        self._active_agents.clear()
        logger.info("🧹 Cleanup complete")
    
    def __repr__(self) -> str:
        return f"LLMOrchestrator(model={self.model}, active_agents={list(self._active_agents.keys())})"


# Backwards compatibility alias
Orchestrator = LLMOrchestrator
