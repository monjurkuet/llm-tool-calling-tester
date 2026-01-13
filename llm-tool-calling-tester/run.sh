#!/bin/bash
# LLM Tool Calling Tester - Run script

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the module
python -m llm_tool_calling_tester "$@"
