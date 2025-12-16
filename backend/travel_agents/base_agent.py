"""
Base Agent Abstract Class

Defines the common interface that all specialized agents must implement.
Provides input/output validation and standardized execution patterns.
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type
import logging

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(backend_dir, '..', 'python-mcp-sandbox-openai-sdk-main', 'src'))
sys.path.insert(0, backend_dir)

from pydantic import BaseModel, ValidationError

from models import (
    AgentResult,
    AgentType,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from config import Config

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all specialized travel agents.
    
    All agents must implement:
    - execute(): Main task execution
    - get_input_schema(): Returns Pydantic model for input validation
    - get_output_schema(): Returns Pydantic model for output validation
    - agent_type: Property returning the AgentType enum value
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the base agent.
        
        Args:
            model: LLM model to use (defaults to Config.DEFAULT_MODEL)
        """
        self.model = model or Config.DEFAULT_MODEL
        self._initialized = False
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Type[BaseModel]:
        """
        Return the Pydantic model class for input validation.
        
        Returns:
            Pydantic model class defining expected input structure
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Type[BaseModel]:
        """
        Return the Pydantic model class for output validation.
        
        Returns:
            Pydantic model class defining expected output structure
        """
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main task.
        
        Args:
            params: Dictionary of parameters matching the input schema
        
        Returns:
            AgentResult with success status and data/error
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up agent resources (MCP servers, connections, etc.)."""
        pass
    
    def validate_input(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate input parameters against the input schema.
        
        Args:
            params: Dictionary of input parameters
        
        Returns:
            ValidationResult with is_valid flag and any issues
        """
        schema = self.get_input_schema()
        issues = []
        
        try:
            # Attempt to validate with Pydantic
            schema(**params)
            return ValidationResult(is_valid=True, issues=[])
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                issues.append(ValidationIssue(
                    field=field,
                    message=error["msg"],
                    severity=ValidationSeverity.ERROR
                ))
            return ValidationResult(is_valid=False, issues=issues)
        except Exception as e:
            issues.append(ValidationIssue(
                field="__root__",
                message=f"Unexpected validation error: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))
            return ValidationResult(is_valid=False, issues=issues)
    
    def validate_output(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate output data against the output schema.
        
        Args:
            data: Dictionary of output data
        
        Returns:
            ValidationResult with is_valid flag and any issues
        """
        schema = self.get_output_schema()
        issues = []
        
        try:
            # Attempt to validate with Pydantic
            schema(**data)
            return ValidationResult(is_valid=True, issues=[])
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                issues.append(ValidationIssue(
                    field=field,
                    message=error["msg"],
                    severity=ValidationSeverity.ERROR
                ))
            return ValidationResult(is_valid=False, issues=issues)
        except Exception as e:
            issues.append(ValidationIssue(
                field="__root__",
                message=f"Unexpected validation error: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))
            return ValidationResult(is_valid=False, issues=issues)
    
    async def execute_with_validation(
        self,
        params: Dict[str, Any],
        max_retries: int = 2
    ) -> AgentResult:
        """
        Execute the agent with input validation, output validation, and retry logic.
        
        Args:
            params: Dictionary of input parameters
            max_retries: Maximum number of retries on validation failure
        
        Returns:
            AgentResult with validation information
        """
        # Validate input first
        input_validation = self.validate_input(params)
        if not input_validation.is_valid:
            logger.warning(f"{self.agent_type.value} agent input validation failed: {input_validation.errors}")
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=f"Input validation failed: {'; '.join(input_validation.errors)}",
                validation=input_validation
            )
        
        # Execute with retry logic
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                result = await self.execute(params)
                
                # Validate output if execution was successful
                if result.success and result.data:
                    output_validation = self.validate_output(result.data)
                    result.validation = output_validation
                    
                    if output_validation.is_valid:
                        result.retry_count = attempt
                        return result
                    else:
                        logger.warning(
                            f"{self.agent_type.value} agent output validation failed (attempt {attempt + 1}): "
                            f"{output_validation.errors}"
                        )
                        last_error = f"Output validation failed: {'; '.join(output_validation.errors)}"
                        # Continue to retry
                else:
                    # Execution failed, return as-is
                    result.retry_count = attempt
                    return result
                    
            except Exception as e:
                logger.error(f"{self.agent_type.value} agent execution error (attempt {attempt + 1}): {e}")
                last_error = str(e)
        
        # All retries exhausted
        return AgentResult(
            agent_type=self.agent_type,
            success=False,
            error=f"Failed after {max_retries + 1} attempts. Last error: {last_error}",
            retry_count=max_retries + 1
        )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"



