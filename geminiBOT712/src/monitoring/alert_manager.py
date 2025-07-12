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
# src/monitoring/system_monitor.py
# Monitors the health of the host system (CPU, RAM, Disk).

import psutil
import asyncio
from utils.logger import get_logger
from .alert_manager import send_system_alert

logger = get_logger(__name__)

class SystemMonitor:
    """Monitors the health of the VPS itself."""
    def __init__(self, cpu_threshold=90.0, mem_threshold=90.0, disk_threshold=95.0):
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        self.disk_threshold = disk_threshold

    async def run(self, interval_seconds: int = 300):
        """Runs the monitoring checks at a specified interval."""
        logger.info("System Health Monitor started.")
        while True:
            # Run synchronous checks in a non-blocking way
            await self.check_health()
            await asyncio.sleep(interval_seconds)
            
    async def check_health(self):
        """Wrapper for running all synchronous health checks."""
        try:
            # CPU Check
            cpu_usage = psutil.cpu_percent(interval=1)
            logger.info(f"System Health - CPU Usage: {cpu_usage}%")
            if cpu_usage > self.cpu_threshold:
                await send_system_alert(f"CPU usage is critical: {cpu_usage}%", "CRITICAL")

            # Memory Check
            mem = psutil.virtual_memory()
            mem_usage = mem.percent
            logger.info(f"System Health - Memory Usage: {mem_usage}%")
            if mem_usage > self.mem_threshold:
                await send_system_alert(f"Memory usage is critical: {mem_usage}%", "CRITICAL")

            # Disk Check
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            logger.info(f"System Health - Disk Usage: {disk_usage}%")
            if disk_usage > self.disk_threshold:
                await send_system_alert(f"Disk space is critical: {disk_usage}% full", "CRITICAL")
        except Exception as e:
            logger.error(f"Error during system health check: {e}", exc_info=True)

```python
# src/monitoring/api_monitor.py
# Monitors the status of external API endpoints.

import httpx
import asyncio
from utils.logger import get_logger
from .alert_manager import send_system_alert
from config.api_config import API_ENDPOINTS

logger = get_logger(__name__)

class ApiMonitor:
    """Periodically checks the health of all critical external API endpoints."""
    def __init__(self):
        self.endpoints_to_check = {
            "YahooFinance": "[https://query1.finance.yahoo.com/v7/finance/quote?symbols=AAPL](https://query1.finance.yahoo.com/v7/finance/quote?symbols=AAPL)",
            "SEC_EDGAR": API_ENDPOINTS['sec_edgar'] + "submissions.json",
        }

    async def run(self, interval_seconds: int = 600):
        """Runs the API health checks at a specified interval."""
        logger.info("External API Monitor started.")
        while True:
            await self.check_all_endpoints()
            await asyncio.sleep(interval_seconds)

    async def check_all_endpoints(self):
        """Checks all configured API endpoints concurrently."""
        tasks = [self.check_endpoint(name, url) for name, url in self.endpoints_to_check.items()]
        await asyncio.gather(*tasks)

    async def check_endpoint(self, name: str, url: str):
        """Checks a single API endpoint."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if 200 <= response.status_code < 300:
                    logger.info(f"API Health Check for {name}: OK (Status: {response.status_code})")
                else:
                    logger.warning(f"API Health Check for {name}: FAILED (Status: {response.status_code})")
                    await send_system_alert(f"External API '{name}' is responding with status {response.status_code}", "WARNING")
        except httpx.RequestError as e:
            logger.error(f"API Health Check for {name}: FAILED (Request Error: {e})")
            await send_system_alert(f"External API '{name}' is unreachable. Error: {e}", "CRITICAL")
