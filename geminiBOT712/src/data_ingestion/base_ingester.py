# src/data_ingestion/base_ingester.py
# Abstract base class for all data ingestion modules.

from abc import ABC, abstractmethod
import asyncio
import httpx
from utils.logger import get_logger
import redis.asyncio as redis
from config.settings import REDIS_HOST, REDIS_PORT
import json

logger = get_logger(__name__)

class BaseIngester(ABC):
    """
    Abstract base class for data ingesters.
    Provides a common interface for fetching data from various sources
    and publishing it to a Redis channel for processing.
    """
    def __init__(self, api_key=None, api_endpoint=None):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.client = httpx.AsyncClient(timeout=10.0)
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    @abstractmethod
    async def fetch_data(self):
        """
        The main method to fetch data from the source.
        This must be implemented by all subclasses.
        """
        pass
        
    async def publish_to_redis(self, channel: str, data: dict):
        """Publishes data to a specified Redis channel."""
        try:
            await self.redis_client.publish(channel, json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to publish to Redis channel '{channel}': {e}")

    async def run(self, interval_seconds: int):
        """
        Runs the data fetching process at a specified interval.
        """
        logger.info(f"Starting ingester for {self.__class__.__name__} with {interval_seconds}s interval.")
        while True:
            try:
                await self.fetch_data()
            except Exception as e:
                logger.error(f"Error in {self.__class__.__name__} ingester: {e}", exc_info=True)
            await asyncio.sleep(interval_seconds)

    async def close(self):
        """Closes the HTTP and Redis clients."""
        await self.client.aclose()
        await self.redis_client.close()
```python
