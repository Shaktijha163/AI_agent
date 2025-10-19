"""
LangGraph Builder - Dynamic workflow orchestration from workflow.json
"""
import json
import re
from typing import Any, Dict, List, TypedDict, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from utils.logger import get_logger
from utils.json_validator import validate_workflow_file
from utils.config_loader import get_config

# Import all agents
from agents.prospect_search_agent import ProspectSearchAgent
from agents.enrichment_agent import DataEnrichmentAgent
from agents.scoring_agent import ScoringAgent
from agents.outreach_content_agent import OutreachContentAgent
from agents.outreach_executor_agent import OutreachExecutorAgent
from agents.response_tracker_agent import ResponseTrackerAgent
from agents.feedback_trainer_agent import FeedbackTrainerAgent

logger = get_logger("langgraph_builder")

# Define workflow state
class WorkflowState(TypedDict):
    """State that flows through the workflow"""
    # Input data
    workflow_name: str
    execution_id: str
    
    # Step outputs (each step adds its output here)
    prospect_search: Dict[str, Any]
    enrichment: Dict[str, Any]
    scoring: Dict[str, Any]
    outreach_content: Dict[str, Any]
    send: Dict[str, Any]
    response_tracking: Dict[str, Any]
    feedback_trainer: Dict[str, Any]
    
    # Execution metadata
    current_step: str
    completed_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[Dict[str, str]], operator.add]
    start_time: str
    end_time: str


class LangGraphWorkflowBuilder:
    """Build and execute LangGraph workflow from workflow.json"""
    
    def __init__(self, workflow_file: str = "workflow.json"):
        self.workflow_file = workflow_file
        self.config = get_config()
        
        # Validate and load workflow
        logger.info(f" Loading workflow from {workflow_file}")
        self.workflow_def = validate_workflow_file(workflow_file)
        
        # Initialize agents
        self._initialize_agents()
        
        # Build graph
        self.graph = None
        self.checkpointer = MemorySaver()
        
        logger.info(f"LangGraphWorkflowBuilder initialized: {self.workflow_def.workflow_name}")
    
    def _initialize_agents(self):
        """Initialize all agents"""
        self.agents = {
            "ProspectSearchAgent": ProspectSearchAgent(agent_id="graph_prospect_search"),
            "DataEnrichmentAgent": DataEnrichmentAgent(agent_id="graph_enrichment"),
            "ScoringAgent": ScoringAgent(agent_id="graph_scoring"),
            "OutreachContentAgent": OutreachContentAgent(agent_id="graph_content"),
            "OutreachExecutorAgent": OutreachExecutorAgent(agent_id="graph_executor"),
            "ResponseTrackerAgent": ResponseTrackerAgent(agent_id="graph_tracker"),
            "FeedbackTrainerAgent": FeedbackTrainerAgent(agent_id="graph_feedback")
        }
        
        logger.info(f" Initialized {len(self.agents)} agents")
    
    def build_graph(self) -> StateGraph:
        """Build LangGraph from workflow definition"""
        logger.info("🏗️  Building LangGraph from workflow definition...")

        workflow = StateGraph(WorkflowState)

        steps = [step.id for step in self.workflow_def.steps]
        node_map = {}  # map logical step_id -> actual node_id used in graph

        for step in self.workflow_def.steps:
            step_id = step.id
            agent_name = step.agent

            # Avoid conflicts with state keys by adding suffix
            node_id = f"{step_id}_node"

            node_map[step_id] = node_id
            logger.info(f"   Adding node: {node_id} ({agent_name})")

            node_func = self._create_node_function(step_id, agent_name, step)
            workflow.add_node(node_id, node_func)

        # Set entry point
        first_node = node_map[steps[0]]
        workflow.set_entry_point(first_node)

        # Add sequential edges
        for i in range(len(steps) - 1):
            workflow.add_edge(node_map[steps[i]], node_map[steps[i + 1]])

        # Last step goes to END
        workflow.add_edge(node_map[steps[-1]], END)

        logger.info(f"Graph built with {len(steps)} nodes")

        self.graph = workflow.compile(checkpointer=self.checkpointer)
        return self.graph


    
    def _create_node_function(self, step_id: str, agent_name: str, step):
        """Create a node function for a specific step"""
        
        def node_function(state: WorkflowState) -> WorkflowState:
            """Execute agent for this step"""
            logger.info(f"\n{'='*60}")
            logger.info(f"🔹 Executing Step: {step_id} ({agent_name})")
            logger.info(f"{'='*60}")
            
            # Get agent
            agent = self.agents.get(agent_name)
            if not agent:
                error_msg = f"Agent {agent_name} not found"
                logger.error(f" {error_msg}")
                state["errors"].append({
                    "step": step_id,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
                return state
            
            # Prepare input by resolving references
            agent_input = self._resolve_input_references(step.inputs, state)
            
            logger.info(f" Input keys: {list(agent_input.keys())}")
            
            # Execute agent
            try:
                output = agent.execute(agent_input)
                
                # Check for errors
                if not output.get('_metadata', {}).get('success', True):
                    error_msg = output.get('error', 'Unknown error')
                    logger.error(f" Agent execution failed: {error_msg}")
                    state["errors"].append({
                        "step": step_id,
                        "error": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    logger.info(f"Step completed successfully")
                    logger.info(f" Output keys: {list(output.keys())}")
                
                # Store output in state
                state[step_id] = output
                state["current_step"] = step_id
                state["completed_steps"] = [step_id]
                
            except Exception as e:
                error_msg = f"Exception during execution: {str(e)}"
                logger.error(f" {error_msg}")
                state["errors"].append({
                    "step": step_id,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return node_function
    
    def _resolve_input_references(self, inputs: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
        """
        Resolve input references like {{prospect_search.output.leads}}
        
        Args:
            inputs: Input dict with possible references
            state: Current workflow state
            
        Returns:
            Resolved input dict
        """
        resolved = {}
        
        for key, value in inputs.items():
            if isinstance(value, str) and "{{" in value and "}}" in value:
                # Extract reference
                match = re.search(r'\{\{(.+?)\}\}', value)
                if match:
                    ref_path = match.group(1)
                    resolved_value = self._get_nested_value(ref_path, state)
                    resolved[key] = resolved_value
                    logger.debug(f"   Resolved: {key} = {{{{ref_path}}}} -> {type(resolved_value)}")
                else:
                    resolved[key] = value
            elif isinstance(value, dict):
                # Recursively resolve nested dicts
                resolved[key] = self._resolve_input_references(value, state)
            elif isinstance(value, list):
                # Resolve list items
                resolved[key] = [
                    self._resolve_input_references(item, state) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    def _get_nested_value(self, path: str, state: WorkflowState) -> Any:
        """
        Get nested value from state using dot notation
        
        Example: "prospect_search.output.leads" -> state["prospect_search"]["leads"]
        """
        parts = path.split('.')
        
        # Handle config references
        if parts[0] == "config":
            if parts[1] == "scoring":
                return self.config.get_scoring_config()
            elif parts[1] == "icp":
                return self.config.get_icp_config()
            else:
                return None
        
        # Navigate through state
        value = state
        for part in parts:
            if isinstance(value, dict):
                # Skip "output" keyword if present (it's implicit in our state)
                if part == "output":
                    continue
                value = value.get(part)
                if value is None:
                    logger.warning(f" Could not resolve path: {path} (stopped at {part})")
                    return None
            else:
                logger.warning(f" Path resolution failed at {part} in {path}")
                return None
        
        return value
    
    def execute(self, initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the complete workflow
        
        Args:
            initial_input: Optional initial input (overrides workflow.json defaults)
            
        Returns:
            Final workflow state
        """
        if not self.graph:
            self.build_graph()
        
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("\n" + "="*60)
        logger.info(f" Starting Workflow Execution: {execution_id}")
        logger.info(f"   Workflow: {self.workflow_def.workflow_name}")
        logger.info(f"   Steps: {len(self.workflow_def.steps)}")
        logger.info("="*60 + "\n")
        
        # Initialize state
        initial_state = {
            "workflow_name": self.workflow_def.workflow_name,
            "execution_id": execution_id,
            "current_step": "",
            "completed_steps": [],
            "errors": [],
            "start_time": datetime.now().isoformat(),
            "end_time": "",
            # Initialize step outputs
            "prospect_search": {},
            "enrichment": {},
            "scoring": {},
            "outreach_content": {},
            "send": {},
            "response_tracking": {},
            "feedback_trainer": {}
        }
        
        # Override with initial input if provided
        if initial_input:
            initial_state.update(initial_input)
        
        # Execute graph
        try:
            config = {"configurable": {"thread_id": execution_id}}
            final_state = self.graph.invoke(initial_state, config)
            
            final_state["end_time"] = datetime.now().isoformat()
            
            # Log summary
            self._log_execution_summary(final_state)
            
            return final_state
            
        except Exception as e:
            logger.error(f" Workflow execution failed: {e}")
            raise
    
    def _log_execution_summary(self, state: WorkflowState):
        """Log execution summary"""
        logger.info("\n" + "="*60)
        logger.info(" WORKFLOW EXECUTION SUMMARY")
        logger.info("="*60)
        
        completed = state.get("completed_steps", [])
        errors = state.get("errors", [])
        
        logger.info(f" Completed Steps: {len(completed)}/{len(self.workflow_def.steps)}")
        for step in completed:
            logger.info(f"   ✓ {step}")
        
        if errors:
            logger.warning(f"\n Errors Encountered: {len(errors)}")
            for error in errors:
                logger.warning(f"   ✗ {error['step']}: {error['error']}")
        
        # Calculate metrics
        start_time = datetime.fromisoformat(state["start_time"])
        end_time = datetime.fromisoformat(state["end_time"])
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"\n Total Duration: {duration:.2f} seconds")
        logger.info(f" Start: {state['start_time']}")
        logger.info(f" End: {state['end_time']}")
        
        # Final results
        if state.get("feedback_trainer"):
            feedback = state["feedback_trainer"]
            logger.info(f"\n Final Results:")
            logger.info(f"   Recommendations: {feedback.get('total_recommendations', 0)}")
            logger.info(f"   Performance: {feedback.get('performance_summary', {}).get('overall_assessment', {}).get('rating', 'unknown')}")
        
        logger.info("\n" + "="*60)
        
        if not errors:
            logger.info(" WORKFLOW COMPLETED SUCCESSFULLY!")
        else:
            logger.warning(" WORKFLOW COMPLETED WITH ERRORS")
        
        logger.info("="*60 + "\n")
    
    def visualize_graph(self, output_file: str = "workflow_graph.png"):
        """
        Visualize the workflow graph
        
        Args:
            output_file: Output file path for graph image
        """
        if not self.graph:
            self.build_graph()
        
        try:
            from IPython.display import Image, display
            
            # Generate mermaid diagram
            mermaid_code = self.graph.get_graph().draw_mermaid()
            
            logger.info(f"Workflow Graph (Mermaid):\n{mermaid_code}")
            
            # Try to save as image (requires additional dependencies)
            try:
                img_data = self.graph.get_graph().draw_mermaid_png()
                with open(output_file, "wb") as f:
                    f.write(img_data)
                logger.info(f" Graph saved to {output_file}")
            except:
                logger.info(" PNG export requires additional dependencies")
                logger.info("   Install with: pip install pygraphviz")
            
        except Exception as e:
            logger.warning(f" Could not visualize graph: {e}")
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow information"""
        return {
            "workflow_name": self.workflow_def.workflow_name,
            "description": self.workflow_def.description,
            "total_steps": len(self.workflow_def.steps),
            "steps": [
                {
                    "id": step.id,
                    "agent": step.agent,
                    "description": step.instructions[:100] + "..."
                }
                for step in self.workflow_def.steps
            ]
        }


def main():
    """Main entry point for workflow execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute AI Agent Workflow")
    parser.add_argument(
        "--workflow",
        default="workflow.json",
        help="Path to workflow JSON file"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualize workflow graph"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show workflow information"
    )
    
    args = parser.parse_args()
    
    # Build workflow
    builder = LangGraphWorkflowBuilder(args.workflow)
    
    # Show info if requested
    if args.info:
        info = builder.get_workflow_info()
        print(json.dumps(info, indent=2))
        return
    
    # Visualize if requested
    if args.visualize:
        builder.visualize_graph()
        return
    
    # Execute workflow
    final_state = builder.execute()
    
    # Save results
    output_file = f"data/workflow_execution_{final_state['execution_id']}.json"
    with open(output_file, "w") as f:
        json.dump(final_state, f, indent=2, default=str)
    
    logger.info(f" Results saved to {output_file}")


if __name__ == "__main__":
    main()