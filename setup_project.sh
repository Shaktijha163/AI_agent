#!/bin/bash

# Create project structure
mkdir -p utils
mkdir -p agents
mkdir -p tools
mkdir -p logs
mkdir -p data

# Create __init__.py files
touch utils/__init__.py
touch agents/__init__.py
touch tools/__init__.py

# Create placeholder files
touch workflow.json
touch config.yaml
touch .env
touch requirements.txt
touch langgraph_builder.py

# Utils
touch utils/json_validator.py
touch utils/logger.py
touch utils/config_loader.py

# Agents
touch agents/base_agent.py
touch agents/prospect_search_agent.py
touch agents/enrichment_agent.py
touch agents/scoring_agent.py
touch agents/outreach_content_agent.py
touch agents/outreach_executor_agent.py
touch agents/response_tracker_agent.py
touch agents/feedback_trainer_agent.py

# Tools
touch tools/clay_api.py
touch tools/apollo_api.py
touch tools/clearbit_api.py
touch tools/gemini_tool.py
touch tools/sendgrid_tool.py
touch tools/google_sheets_tool.py

echo " Project structure created successfully!"