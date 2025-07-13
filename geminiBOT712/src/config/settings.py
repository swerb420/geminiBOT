# config/settings.py
# General application settings and logging configuration.

import os
from dotenv import load_dotenv
import logging
import sys

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
```python
# config/api_config.py
# Manages API keys and endpoints for various data sources.

# In a real system, these would be loaded from a secure vault or encrypted file.
# For this example, we'll use placeholders.
# The `utils/encryption.py` module will handle the actual secure loading.

API_KEYS = {
    "unusual_whales": "YOUR_UNUSUAL_WHALES_API_KEY",
    "bigshort": "YOUR_BIGSHORT_API_KEY",
    "stalkchain": "YOUR_STALKCHAIN_API_KEY",
    "twitter": {
        "api_key": "YOUR_TWITTER_API_KEY",
        "api_secret_key": "YOUR_TWITTER_API_SECRET_KEY",
        "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
        "access_token_secret": "YOUR_TWITTER_ACCESS_TOKEN_SECRET"
    },
    "sec": {
        "user_agent": "Your Name Your-Email@example.com"
    }
    # Add other APIs here
}

API_ENDPOINTS = {
    "unusual_whales": "https://api.unusualwhales.com/v2/",
    "bigshort": "https://api.bigshort.com/v1/",
    "stalkchain": "https://api.stalkchain.io/v1/",
    "sec_edgar": "https://data.sec.gov/submissions/",
    "federal_reserve": "https://api.stlouisfed.org/fred/",
    "google_trends": "https://trends.google.com/trends/api/",
    "yahoo_finance": "https://query1.finance.yahoo.com/"
}
```python
# config/trading_config.py
# Defines risk management parameters and trading strategies.

# --- Risk Management ---
MAX_RISK_PER_TRADE = 0.02  # 2% of total capital
MAX_DAILY_LOSS_LIMIT = 0.08 # 8% of total capital
MAX_PORTFOLIO_EXPOSURE = 0.50 # Max 50% of capital deployed at any time

# --- Position Sizing ---
# Options: 'fixed_fractional', 'kelly_criterion'
POSITION_SIZING_STRATEGY = 'kelly_criterion'

# --- Signal Generation ---
MIN_CONFIDENCE_SCORE = 85.0 # Only execute signals with confidence >= 85%
REQUIRED_CONFIRMING_INDICATORS = 3 # Minimum number of indicators for a valid signal

# --- Execution ---
# Set to 'paper' for testing, 'live' for real trading
TRADING_MODE = 'paper'
```python
# src/execution/telegram_bot.py
# Handles all interactions with the user via the Telegram bot.

import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.logger import get_logger

logger = get_logger(__name__)

class TelegramBot:
    """
    The Telegram bot for user interaction, alerts, and system control.
    """
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not found. The bot will not start.")
            self.application = None
            return
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Sets up the command and message handlers for the bot."""
        if not self.application:
            return
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        # Add more handlers for other commands (e.g., trades, performance)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for the /start command."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}! I am your autonomous trading assistant. "
            "Type /help to see available commands."
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for the /status command. Reports system status."""
        # In a real implementation, this would query other system components.
        await update.message.reply_text(
            "System Status: OPERATIONAL\n"
            "Trading Mode: paper\n"
            "Active Signals: 0\n"
            "Open Trades: 0"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for the /help command."""
        help_text = (
            "Available Commands:\n"
            "/start - Initialize the bot\n"
            "/status - Get the current system status\n"
            "/help - Show this help message\n"
            # Add descriptions for other commands
        )
        await update.message.reply_text(help_text)

    async def send_alert(self, message: str):
        """Sends an alert message to the predefined chat ID."""
        if not self.application or not TELEGRAM_CHAT_ID:
            logger.warning(f"Cannot send alert, bot not configured or chat ID missing. Message: {message}")
            return
        try:
            bot = self.application.bot
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}", exc_info=True)

    async def start(self):
        """Starts the bot's polling loop."""
        if not self.application:
            return
        logger.info("Telegram bot started...")
        # The bot runs in the background
        self.application.run_polling()
        # Send a startup message
        await self.send_alert("Trading System is now online.")


    async def stop(self):
        """Stops the bot."""
        if not self.application:
            return
        logger.info("Stopping Telegram bot...")
        # The stop is handled by the application's lifecycle
