# src/data_ingestion/bigshort.py
# Data ingester for TheBigShort API (institutional flow).

from .base_ingester import BaseIngester
from config.api_config import API_KEYS, API_ENDPOINTS
from utils.logger import get_logger
import json

logger = get_logger(__name__)

class BigShortIngester(BaseIngester):
    """
    Fetches institutional flow data from TheBigShort API and
    publishes it to a Redis channel.
    """
    def __init__(self):
        # In a production system, use the KeyManager
        api_key = API_KEYS.get("bigshort") # Placeholder for now
        api_endpoint = API_ENDPOINTS.get("bigshort")
        super().__init__(api_key, api_endpoint)
        if not api_key or "YOUR_BIGSHORT" in api_key:
            logger.warning("BigShort API key not found or is a placeholder. Ingester will be disabled.")
            self.api_key = None

    async def fetch_data(self):
        """
        Fetches the latest institutional flow data.
        """
        if not self.api_key:
            return

        # This is a hypothetical endpoint. You must replace it with the actual one from their docs.
        url = f"{self.api_endpoint}flows/latest"
        params = {"token": self.api_key}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            flow_data = response.json().get('data', [])

            if not flow_data:
                logger.info("No new institutional flow from BigShort.")
                return

            logger.info(f"Successfully fetched {len(flow_data)} institutional flow records.")
            
            for record in flow_data:
                # Publish each record to its own Redis channel
                await self.publish_to_redis('institutional_flow', record)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching from BigShort: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"An error occurred while fetching from BigShort: {e}", exc_info=True)
```python
