# src/data_ingestion/unusual_whales.py
# Data ingester for the Unusual Whales API.

from .base_ingester import BaseIngester
from config.api_config import API_KEYS, API_ENDPOINTS
from utils.logger import get_logger
import json

logger = get_logger(__name__)

class UnusualWhalesIngester(BaseIngester):
    """
    Fetches unusual options flow data from the Unusual Whales API
    and publishes it to a Redis channel.
    """
    def __init__(self):
        # In a production system, use the KeyManager to get keys
        api_key = API_KEYS.get("unusual_whales") # Placeholder for now
        api_endpoint = API_ENDPOINTS.get("unusual_whales")
        super().__init__(api_key, api_endpoint)
        if not api_key or "YOUR_UNUSUAL" in api_key:
            logger.warning("Unusual Whales API key not found or is a placeholder. Ingester will be disabled.")
            self.api_key = None

    async def fetch_data(self):
        """
        Fetches the latest unusual options flow data and publishes it.
        """
        if not self.api_key:
            return

        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Example endpoint for fetching the most recent trades
        url = f"{self.api_endpoint}option-trades/real-time" 

        params = {'limit': 50} # Limit the number of trades per fetch

        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            flow_records = response.json().get('data', [])
            
            if not flow_records:
                logger.info("No new unusual flow records from Unusual Whales.")
                return

            logger.info(f"Successfully fetched {len(flow_records)} unusual flow records.")
            
            # Publish each record to Redis for the AI pipeline
            for record in flow_records:
                await self.publish_to_redis('options_flow', record)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching from Unusual Whales: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"An error occurred while fetching from Unusual Whales: {e}", exc_info=True)
```python
