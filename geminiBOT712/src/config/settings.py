# config/settings.py
# General application settings and logging configuration.

import os
import logging
import sys

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*_args, **_kwargs):
        """Fallback no-op if python-dotenv is unavailable."""
        pass

# Load environment variables from .env file
load_dotenv()

# --- General Settings ---
APP_NAME = "Autonomous Trading System"
VERSION = "1.0.0"

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/trading_db")

# --- Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # Your personal chat ID for alerts

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging():
    """
    Configures the root logger for the application.
    """
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("trading_system.log")
        ]
    )
    # Suppress noisy library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


# --- Security ---
# This is a placeholder for the path to your encrypted keys file
ENCRYPTED_KEYS_PATH = os.getenv("ENCRYPTED_KEYS_PATH", "/app/config/encrypted_api_keys.json")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") # MUST be set in .env

def verify_encrypted_keys():
    if not os.path.exists(ENCRYPTED_KEYS_PATH):
        raise FileNotFoundError(
            f"Encrypted keys file missing at {ENCRYPTED_KEYS_PATH}. Run scripts/encrypt_keys.py"
        )

# --- Execution Mode ---
# Determines whether the system trades in paper or live mode.
TRADING_MODE = os.getenv("TRADING_MODE", "paper")
