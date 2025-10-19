"""
Base Agent class - Abstract interface for all workflow agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
import json
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from utils.logger import get_logger
from utils.config_loader import get_config

class AgentInput(BaseModel):
    """Base input model for agents"""
    pass

class AgentOutput(BaseModel):
    """Base output model for agents"""
    agent_name: str
    execution_time: float
    timestamp: str
    success: bool
    error_message: Optional[str] = None

class BaseAgent(ABC):
    """Abstract base class for all workflow agents"""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.agent_name = self.__class__.__name__
        self.config = config or {}
        self.logger = get_logger(self.agent_name)
        self.config_loader = get_config()
        
        # Agent metadata
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = None
        
        # Initialize agent-specific setup
        self._initialize()
    
    def _initialize(self):
        """Override this for agent-specific initialization"""
        pass
    
    @abstractmethod
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data structure - must be implemented by subclass"""
        pass
    
    @abstractmethod
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Core agent logic - must be implemented by subclass"""
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method with error handling and logging
        
        Args:
            input_data: Input dictionary for the agent
            
        Returns:
            Output dictionary with results
        """
        start_time = time.time()
        self.logger.log_agent_start(self.agent_name, input_data)
        
        try:
            # Validate input
            if not self._validate_input(input_data):
                raise ValueError(f"Input validation failed for {self.agent_name}")
            
            # Execute agent logic
            output_data = self._execute(input_data)
            
            # Add metadata
            execution_time = time.time() - start_time
            output_data['_metadata'] = {
                'agent_name': self.agent_name,
                'agent_id': self.agent_id,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            # Update stats
            self.execution_count += 1
            self.total_execution_time += execution_time
            self.last_execution_time = execution_time
            
            self.logger.log_agent_complete(self.agent_name, output_data, execution_time)
            return output_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_agent_error(self.agent_name, e)
            
            # Return error output
            return {
                'error': str(e),
                'error_type': type(e).__name__,
                '_metadata': {
                    'agent_name': self.agent_name,
                    'agent_id': self.agent_id,
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error_message': str(e)
                }
            }
    
    def _log_reasoning(self, step: str, thought: str):
        """Log agent reasoning step (ReAct pattern)"""
        self.logger.debug(f" Reasoning | {step}: {thought}")
    
    def _log_action(self, action: str, details: Dict[str, Any]):
        """Log agent action"""
        self.logger.info(f"Action | {action} | {json.dumps(details, default=str)}")
    
    def _log_observation(self, observation: str):
        """Log agent observation"""
        self.logger.info(f"Observation | {observation}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics"""
        return {
            'agent_name': self.agent_name,
            'execution_count': self.execution_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': (
                self.total_execution_time / self.execution_count 
                if self.execution_count > 0 else 0
            ),
            'last_execution_time': self.last_execution_time
        }
    
    def _get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a specific tool"""
        return self.config_loader.get_api_config(tool_name)
    
    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self.config_loader.get_workflow_config().enable_mock_mode
    
    def _is_dry_run(self) -> bool:
        """Check if running in dry run mode"""
        return self.config_loader.get_workflow_config().dry_run