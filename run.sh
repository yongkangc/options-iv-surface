#!/bin/bash

# Install dependencies with uv and run the IV surface script

echo "Setting up environment with uv..."

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create virtual environment and install dependencies
echo "Creating virtual environment and installing dependencies..."
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r pyproject.toml

# Run the main script
echo "Running IV surface construction..."
python main.py

echo "Done!"