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
# src/ai_analysis/sentiment_analyzer.py
# Performs sentiment analysis on text data using a pre-trained model.

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from utils.logger import get_logger
import torch

logger = get_logger(__name__)

class SentimentAnalyzer:
    """
    A wrapper for a Hugging Face sentiment analysis pipeline.
    Uses a model fine-tuned for financial news and auto-detects GPU.
    """
    def __init__(self, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        """
        Loads the sentiment analysis model and tokenizer.
        Handles errors gracefully and attempts to use GPU if available.
        """
        try:
            # Check for GPU
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            logger.info(f"Loading sentiment analysis model: {self.model_name} on {device_name}...")
            
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=device
            )
            logger.info("Sentiment analysis model loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load sentiment analysis model: {e}", exc_info=True)
            logger.warning("Sentiment analysis will be disabled.")

    def analyze(self, text: str) -> dict:
        """
        Analyzes the sentiment of a given piece of text.

        Returns:
            A dictionary with 'label' and 'score', or an empty dict on failure.
        """
        if not self.pipeline:
            return {}

        if not text or not isinstance(text, str):
            return {}

        try:
            # The pipeline expects a list of texts
            results = self.pipeline([text])
            # Normalize label to be consistently uppercase
            result = results[0] if results else {}
            if 'label' in result:
                result['label'] = result['label'].upper() # e.g., POSITIVE, NEGATIVE
            return result
        except Exception as e:
            logger.error(f"Error during sentiment analysis for text: '{text[:50]}...': {e}", exc_info=True)
            return {}

# Example usage:
if __name__ == '__main__':
    analyzer = SentimentAnalyzer()
    if analyzer.pipeline:
        news_headline = "AAPL stock surges after record-breaking iPhone sales report."
        sentiment = analyzer.analyze(news_headline)
        print(f"Headline: '{news_headline}'")
        print(f"Sentiment: {sentiment}")

        news_headline_2 = "Market plunges as new inflation data spooks investors."
        sentiment_2 = analyzer.analyze(news_headline_2)
        print(f"Headline: '{news_headline_2}'")
        print(f"Sentiment: {sentiment_2}")
