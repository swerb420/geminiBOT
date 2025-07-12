# scripts/setup.sh
# A simple script to help with initial project setup.

#!/bin/bash

echo "--- Autonomous Trading System Setup ---"

# Check for Python 3.11+
if ! command -v python3.11 &> /dev/null
then
    echo "Python 3.11 could not be found. Please install it."
    # exit 1 # Uncomment to enforce check
fi

# Check for Docker
if ! command -v docker &> /dev/null
then
    echo "Docker could not be found. Please install Docker and Docker Compose."
    # exit 1 # Uncomment to enforce check
fi

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    echo "Copying .env.example to .env. Please fill it out with your credentials."
    cp .env.example .env
else
    echo ".env file already exists. Skipping."
fi

# Remind user about encryption
echo ""
echo "IMPORTANT: After filling out your .env file, you MUST encrypt your API keys."
echo "Run this command: python scripts/encrypt_keys.py"
echo ""
echo "Setup complete. Activate the virtual environment with 'source venv/bin/activate'."

