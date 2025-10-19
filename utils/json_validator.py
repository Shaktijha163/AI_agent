"""
Workflow JSON Schema Validator
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator
from utils.logger import get_logger

logger = get_logger("json_validator")

class ToolConfig(BaseModel):
    """Tool configuration schema"""
    name: str
    config: Dict[str, Any]

class OutputSchema(BaseModel):
    """Output schema definition"""
    schema_dict: Dict[str, Any] = Field(alias="output_schema")
    
    class Config:
        populate_by_name = True

class WorkflowStep(BaseModel):
    """Individual workflow step schema"""
    id: str
    agent: str
    inputs: Dict[str, Any]
    instructions: str
    tools: List[ToolConfig] = Field(default_factory=list)
    output_schema: Dict[str, Any]
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate step ID format"""
        if not v.replace('_', '').isalnum():
            raise ValueError(f"Step ID must be alphanumeric with underscores: {v}")
        return v
    
    @field_validator('agent')
    @classmethod
    def validate_agent(cls, v: str) -> str:
        """Validate agent name"""
        valid_agents = [
            "ProspectSearchAgent",
            "DataEnrichmentAgent",
            "ScoringAgent",
            "OutreachContentAgent",
            "OutreachExecutorAgent",
            "ResponseTrackerAgent",
            "FeedbackTrainerAgent"
        ]
        if v not in valid_agents:
            logger.warning(f" Agent {v} not in predefined list: {valid_agents}")
        return v

class WorkflowDefinition(BaseModel):
    """Main workflow definition schema"""
    workflow_name: str
    description: str
    steps: List[WorkflowStep]
    
    @field_validator('steps')
    @classmethod
    def validate_steps(cls, v: List[WorkflowStep]) -> List[WorkflowStep]:
        """Validate workflow steps"""
        if not v:
            raise ValueError("Workflow must have at least one step")
        
        # Check for duplicate IDs
        step_ids = [step.id for step in v]
        if len(step_ids) != len(set(step_ids)):
            duplicates = [sid for sid in step_ids if step_ids.count(sid) > 1]
            raise ValueError(f"Duplicate step IDs found: {duplicates}")
        
        return v

class WorkflowValidator:
    """Validate workflow.json against schema"""
    
    def __init__(self, workflow_file: str = "workflow.json"):
        self.workflow_file = Path(workflow_file)
        self.workflow_data: Optional[Dict[str, Any]] = None
        self.workflow_definition: Optional[WorkflowDefinition] = None
    
    def load_workflow(self) -> Dict[str, Any]:
        """Load workflow JSON file"""
        if not self.workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {self.workflow_file}")
        
        try:
            with open(self.workflow_file, 'r') as f:
                self.workflow_data = json.load(f)
            logger.info(f" Loaded workflow from {self.workflow_file}")
            return self.workflow_data
        except json.JSONDecodeError as e:
            logger.error(f" Invalid JSON in workflow file: {e}")
            raise
    
    def validate(self) -> bool:
        """Validate workflow against schema"""
        if not self.workflow_data:
            self.load_workflow()
        
        try:
            self.workflow_definition = WorkflowDefinition(**self.workflow_data)
            logger.info(f" Workflow validation passed: {self.workflow_definition.workflow_name}")
            logger.info(f"   Total steps: {len(self.workflow_definition.steps)}")
            return True
        except ValidationError as e:
            logger.error(f" Workflow validation failed:")
            for error in e.errors():
                logger.error(f"   - {error['loc']}: {error['msg']}")
            raise
    
    def get_workflow(self) -> WorkflowDefinition:
        """Get validated workflow definition"""
        if not self.workflow_definition:
            self.validate()
        return self.workflow_definition
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get specific workflow step"""
        if not self.workflow_definition:
            self.validate()
        
        for step in self.workflow_definition.steps:
            if step.id == step_id:
                return step
        
        logger.warning(f"  Step {step_id} not found in workflow")
        return None
    
    def validate_dependencies(self) -> bool:
        """Validate that step dependencies exist"""
        if not self.workflow_definition:
            self.validate()
        
        step_ids = {step.id for step in self.workflow_definition.steps}
        
        for step in self.workflow_definition.steps:
            # Check if input references exist
            for key, value in step.inputs.items():
                if isinstance(value, str) and "{{" in value and "}}" in value:
                    # Extract referenced step ID (e.g., "{{prospect_search.output.leads}}")
                    ref_step_id = value.split("{{")[1].split(".")[0]
                    if ref_step_id != "config" and ref_step_id not in step_ids:
                        logger.error(f"Step {step.id} references non-existent step: {ref_step_id}")
                        return False
        
        logger.info(" All step dependencies validated")
        return True


def validate_workflow_file(workflow_file: str = "workflow.json") -> WorkflowDefinition:
    """Convenience function to validate workflow file"""
    validator = WorkflowValidator(workflow_file)
    validator.validate()
    validator.validate_dependencies()
    return validator.get_workflow()