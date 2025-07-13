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
echo "---"
```ini
# .env.example
# Example environment variables. Copy this to .env and fill in your values.

# --- PostgreSQL Database ---
# Make sure these match the values in docker-compose.yml
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=trading_db
DATABASE_URL=postgresql://trading_user:your_strong_password@db:5432/trading_db

# --- Redis ---
REDIS_HOST=redis
REDIS_PORT=6379

# --- Telegram Bot ---
# Get this from BotFather on Telegram
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
# Get your chat ID from a bot like @userinfobot
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID

# --- API Keys (will be encrypted) ---
# It's recommended to set these here for the encryption script,
# but they will be loaded from the encrypted file at runtime.
UNUSUAL_WHALES_API_KEY=YOUR_UNUSUAL_WHALES_API_KEY
# Add other keys as needed...

# --- Security ---
# A 32-byte key for Fernet encryption.
# Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=YOUR_32_BYTE_ENCRYPTION_KEY

# --- General ---
LOG_LEVEL=INFO # DEBUG, INFO, WARNING, ERROR, CRITICAL
```gitignore
# .gitignore

# Byte-compiled / optimized / C extensions
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Docker
.dockerignore
docker-compose.override.yml

# Logs
*.log
logs/

# Database
# For example, SQLite databases
*.sqlite3
*.db

# Encrypted files
encrypted_*.json
```text
# requirements.txt

# Core
python-dotenv
asyncio

# Web & API
httpx
fastapi
uvicorn
nginx

# Database
sqlalchemy
psycopg2-binary
redis

# AI & Machine Learning
torch
transformers
scikit-learn
pandas
numpy

# Telegram
python-telegram-bot

# Security
cryptography

# Utilities
alembic # For database migrations
