"""
Agent Registry

Provides a pluggable registration system for specialized agents.
Allows dynamic registration and retrieval of agent classes.
"""

import os
import sys
from typing import Dict, Type, Optional, List
import logging

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from models import AgentType
from .base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for pluggable agents.
    
    Allows registration and retrieval of agent classes by name or type.
    Supports lazy loading of agents to avoid circular imports.
    """
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, name: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class.
        
        Args:
            name: Unique name for the agent (e.g., "destination", "flight")
            agent_class: The agent class to register (must extend BaseAgent)
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"Agent class must extend BaseAgent, got {agent_class}")
        
        if name in cls._agents:
            logger.warning(f"Overwriting existing agent registration for '{name}'")
        
        cls._agents[name] = agent_class
        logger.info(f"Registered agent: {name} -> {agent_class.__name__}")
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAgent]]:
        """
        Get an agent class by name.
        
        Args:
            name: Name of the agent to retrieve
        
        Returns:
            Agent class or None if not found
        """
        cls._ensure_initialized()
        return cls._agents.get(name)
    
    @classmethod
    def get_by_type(cls, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
        """
        Get an agent class by AgentType enum.
        
        Args:
            agent_type: AgentType enum value
        
        Returns:
            Agent class or None if not found
        """
        return cls.get(agent_type.value)
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """
        List all registered agent names.
        
        Returns:
            List of registered agent names
        """
        cls._ensure_initialized()
        return list(cls._agents.keys())
    
    @classmethod
    def has_agent(cls, name: str) -> bool:
        """
        Check if an agent is registered.
        
        Args:
            name: Name of the agent to check
        
        Returns:
            True if agent is registered
        """
        cls._ensure_initialized()
        return name in cls._agents
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents (useful for testing)."""
        cls._agents.clear()
        cls._initialized = False
        logger.info("Cleared agent registry")
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure default agents are registered."""
        if cls._initialized:
            return
        
        cls._register_default_agents()
        cls._initialized = True
    
    @classmethod
    def _register_default_agents(cls) -> None:
        """Register all default agents."""
        # Import here to avoid circular imports
        try:
            from .destination_agent import DestinationAgent
            cls.register("destination", DestinationAgent)
        except ImportError as e:
            logger.warning(f"Could not import DestinationAgent: {e}")
        
        try:
            from .flight_agent import FlightAgent
            cls.register("flight", FlightAgent)
        except ImportError as e:
            logger.warning(f"Could not import FlightAgent: {e}")
        
        try:
            from .hotel_agent import HotelAgent
            cls.register("hotel", HotelAgent)
        except ImportError as e:
            logger.warning(f"Could not import HotelAgent: {e}")
        
        try:
            from .transport_agent import TransportAgent
            cls.register("transport", TransportAgent)
        except ImportError as e:
            logger.warning(f"Could not import TransportAgent: {e}")


def get_agent(name: str, model: Optional[str] = None) -> Optional[BaseAgent]:
    """
    Convenience function to get and instantiate an agent.
    
    Args:
        name: Name of the agent
        model: Optional model override
    
    Returns:
        Instantiated agent or None if not found
    """
    agent_class = AgentRegistry.get(name)
    if agent_class:
        return agent_class(model=model)
    return None


def get_agent_by_type(agent_type: AgentType, model: Optional[str] = None) -> Optional[BaseAgent]:
    """
    Convenience function to get and instantiate an agent by type.
    
    Args:
        agent_type: AgentType enum value
        model: Optional model override
    
    Returns:
        Instantiated agent or None if not found
    """
    return get_agent(agent_type.value, model=model)



