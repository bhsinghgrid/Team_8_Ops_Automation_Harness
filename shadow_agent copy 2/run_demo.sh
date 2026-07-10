#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

VENV_DIR=".venv"

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Run the agent demo
echo "Running agent demo..."
python3 run_agent_demo.py

echo "Agent demo completed."
