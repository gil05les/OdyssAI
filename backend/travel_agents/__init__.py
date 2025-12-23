"""
Agent modules for the travel planning system.

Provides a pluggable architecture for specialized travel agents coordinated
by an LLM-powered orchestrator with input/output validation.
"""

# Base classes and registry
from .base_agent import BaseAgent
from .agent_registry import AgentRegistry, get_agent, get_agent_by_type

# Specialized agents
from .destination_agent import DestinationAgent
from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent
from .transport_agent import TransportAgent
from .activities_agent import ActivitiesAgent

# Orchestrators
from .llm_orchestrator import LLMOrchestrator, Orchestrator
from .orchestrator import Orchestrator as LegacyOrchestrator

__all__ = [
    # Base classes
    'BaseAgent',
    'AgentRegistry',
    'get_agent',
    'get_agent_by_type',
    
    # Agents
    'DestinationAgent',
    'FlightAgent',
    'HotelAgent',
    'TransportAgent',
    'ActivitiesAgent',
    
    # Orchestrators
    'LLMOrchestrator',
    'Orchestrator',
    'LegacyOrchestrator',
]

