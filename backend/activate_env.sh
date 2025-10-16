#!/bin/bash

# Auto-activate Poetry environment for landingpage backend
# Usage: source activate_env.sh

# Get the Poetry environment path
POETRY_ENV_PATH=$(poetry env info --path 2>/dev/null)

if [ -z "$POETRY_ENV_PATH" ]; then
    echo "Error: Poetry environment not found. Make sure you're in the backend directory and Poetry is installed."
    exit 1
fi

# Check if the activate script exists
ACTIVATE_SCRIPT="$POETRY_ENV_PATH/bin/activate"

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "Error: Poetry environment not properly set up. Run 'poetry install' first."
    exit 1
fi

# Activate the environment
echo "Activating Poetry environment: $POETRY_ENV_PATH"
source "$ACTIVATE_SCRIPT"

# Verify activation
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Poetry environment activated successfully!"
    echo "Python: $(which python)"
    echo "Django version: $(python -c "import django; print(django.get_version())" 2>/dev/null || echo "Django not installed")"
else
    echo "❌ Failed to activate Poetry environment"
    exit 1
fi
