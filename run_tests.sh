#!/bin/bash

# Run tests for IV surface construction

echo "Setting up test environment..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    uv venv
    source .venv/bin/activate
    uv pip install -e .
fi

echo ""
echo "Running unit tests..."
echo "===================="
pytest test_iv_calculator.py -v

echo ""
echo "Running integration tests..."
echo "==========================="
pytest test_integration.py -v

echo ""
echo "Running all tests with coverage..."
echo "=================================="
pytest --cov=. --cov-report=term-missing --cov-report=html

echo ""
echo "Test coverage report generated in htmlcov/index.html"
echo "Done!"