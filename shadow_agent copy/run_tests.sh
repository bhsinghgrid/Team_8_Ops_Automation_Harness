#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
PYTHON_VERSION="3.10"
VENV_DIR=".venv"

# --- Functions ---

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# --- Main Script ---

# 1. Check for Python
if command_exists python3 && python3 -c "import sys; assert sys.version_info >= (3, 9)" ; then
    PYTHON_CMD="python3"
elif command_exists python && python -c "import sys; assert sys.version_info >= (3, 9)" ; then
    PYTHON_CMD="python"
else
    echo "Python 3.9+ is required. Please install it."
    exit 1
fi

# 2. Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# 3. Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 4. Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Run tests
echo "Running tests..."
export PYTHONPATH=src
pytest

echo "Tests completed successfully."
