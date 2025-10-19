#!/usr/bin/env python3
"""
CLI tool to run the AI Agent Workflow
"""
import argparse
import json
import sys
from datetime import datetime

from utils.logger import get_logger
from langgraph_builder import LangGraphWorkflowBuilder

logger = get_logger("workflow_runner")

def run_workflow(
    workflow_file: str = "workflow.json",
    save_results: bool = True,
    max_leads: int = None
):
    """
    Run the complete workflow
    
    Args:
        workflow_file: Path to workflow.json
        save_results: Whether to save results to file
        max_leads: Maximum number of leads to process (overrides config)
        
    Returns:
        Final workflow state
    """
    try:
        # Initialize workflow builder
        builder = LangGraphWorkflowBuilder(workflow_file)

        # Inject runtime overrides
        initial_input = {}
        if max_leads:
            initial_input["config_overrides"] = {"max_leads": max_leads}
            logger.info(f" Limiting to {max_leads} leads")

        # Execute workflow
        final_state = builder.execute(initial_input=initial_input)

        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/run_output_{timestamp}.json"
            with open(output_file, "w") as f:
                json.dump(final_state, f, indent=2, default=str)
            logger.info(f" Results saved to {output_file}")

        # Summarize
        completed_steps = final_state.get("completed_steps", [])
        errors = final_state.get("errors", [])
        logger.info(f"Completed Steps: {len(completed_steps)}")
        if errors:
            logger.warning(f"  {len(errors)} errors encountered")

        return final_state

    except Exception as e:
        logger.error(f" Workflow execution failed: {e}")
        sys.exit(1)


def main():
    """Command-line entry point"""
    parser = argparse.ArgumentParser(description="Run the AI Agent Workflow")

    parser.add_argument(
        "--workflow",
        default="workflow.json",
        help="Path to workflow JSON file"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save results to a JSON file"
    )
    parser.add_argument(
        "--max-leads",
        type=int,
        default=None,
        help="Limit the number of leads processed"
    )

    args = parser.parse_args()

    run_workflow(
        workflow_file=args.workflow,
        save_results=not args.no_save,
        max_leads=args.max_leads
    )


if __name__ == "__main__":
    main()
