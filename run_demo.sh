#!/bin/bash
# Run the IT Glue to ServiceNow Migration Demo

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the migration demo
echo "Running migration demo..."
python main.py

# Deactivate virtual environment
deactivate

echo "Demo completed!"