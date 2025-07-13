# src/data_ingestion/federal_reserve.py
# Data ingester for the Federal Reserve Economic Data (FRED) API.

from .base_ingester import BaseIngester
from config.api_config import API_KEYS, API_ENDPOINTS
from utils.logger import get_logger
import json

logger = get_logger(__name__)

class FederalReserveIngester(BaseIngester):
    """
    Fetches key economic indicators from the FRED API.
    e.g., Interest Rates, Inflation (CPI), Unemployment.
    """
    def __init__(self, series_ids: list):
        """
        Args:
            series_ids (list): A list of FRED series IDs to track.
                               e.g., 'DFF' (Fed Funds Rate), 'CPIAUCSL' (CPI).
        """
        # In a real system, use the KeyManager
        api_key = API_KEYS.get("federal_reserve", {}).get("api_key") # Hypothetical key structure
        super().__init__(api_key=api_key, api_endpoint=API_ENDPOINTS.get("federal_reserve"))
        self.series_ids = series_ids
        if not self.api_key:
            logger.warning("FRED API key not found. Ingester will be disabled.")

    async def fetch_series(self, series_id: str):
        """Fetches the latest observation for a single economic series."""
        if not self.api_key:
            return

        url = f"{self.api_endpoint}series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc"
        }
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            latest_observation = data.get('observations', [{}])[0]
            
            if latest_observation:
                logger.info(f"Fetched FRED data for {series_id}: {latest_observation['value']} on {latest_observation['date']}")
                # Publish this economic data for the AI pipeline to analyze its impact
                await self.publish_to_redis('economic_data', {"series_id": series_id, **latest_observation})

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching from FRED for {series_id}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}", exc_info=True)

    async def fetch_data(self):
        """Fetches data for all configured FRED series concurrently."""
        tasks = [self.fetch_series(sid) for sid in self.series_ids]
        await asyncio.gather(*tasks)
