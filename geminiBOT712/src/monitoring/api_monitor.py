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
