# src/monitoring/alert_manager.py
# A centralized manager for sending alerts.

from execution.telegram_bot import TelegramBot
from utils.logger import get_logger

logger = get_logger(__name__)

class AlertManager:
    """
    A singleton class to handle sending alerts via various channels.
    Currently supports Telegram.
    """
    _instance = None
    _telegram_bot = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlertManager, cls).__new__(cls)
            cls._telegram_bot = TelegramBot()
        return cls._instance

    async def send_alert(self, message: str, level: str = "INFO"):
        """Sends an alert."""
        formatted_message = f"[{level}] {message}"
        logger.info(f"Sending Alert: {formatted_message}")
        await self._telegram_bot.send_alert(formatted_message)

async def send_system_alert(message: str, level: str = "INFO"):
    """Convenience function to access the AlertManager singleton."""
    await AlertManager().send_alert(message, level)

```python