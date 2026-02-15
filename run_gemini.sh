#!/bin/bash
# Wrapper script to run Gemini CLI with the correct virtual environment activated.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Path to the virtual environment
VENV_PATH="$PROJECT_ROOT/.venv_fix"

# Check if the virtual environment exists
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it or update this script."
    exit 1
fi

# Run the Gemini CLI, passing all arguments
# Assuming 'gemini' is in the path after activation or installed globally
if command -v gemini &> /dev/null; then
    gemini "$@"
else
    echo "Error: 'gemini' command not found."
    echo "Please install it: npm install -g @google/gemini-cli"
    exit 1
fi
