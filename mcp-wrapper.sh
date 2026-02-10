#!/bin/bash

# Debug wrapper for MCP server
LOG_FILE="$HOME/autotrader_mcp_wrapper.log"

echo "$(date) | Wrapper started" >> "$LOG_FILE"
echo "$(date) | PWD: $(pwd)" >> "$LOG_FILE"
echo "$(date) | Args: $@" >> "$LOG_FILE"
echo "$(date) | PATH: $PATH" >> "$LOG_FILE"

cd /Users/joecaruso/Projects/auto-trader || {
    echo "$(date) | ERROR: Failed to cd to project directory" >> "$LOG_FILE"
    exit 1
}

echo "$(date) | Changed to: $(pwd)" >> "$LOG_FILE"
echo "$(date) | Executing: /Users/joecaruso/.local/bin/poetry run trader mcp serve" >> "$LOG_FILE"

exec /Users/joecaruso/.local/bin/poetry run trader mcp serve 2>> "$LOG_FILE"
