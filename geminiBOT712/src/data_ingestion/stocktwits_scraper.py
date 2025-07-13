# src/data_ingestion/stocktwits_scraper.py
# Data ingester for the Stocktwits real-time stream.

from .base_ingester import BaseIngester
from utils.logger import get_logger
import httpx
import json

logger = get_logger(__name__)

class StocktwitsIngester(BaseIngester):
    """
    Connects to the Stocktwits stream API for a given symbol.
    """
    def __init__(self, symbols_to_track: list):
        super().__init__()
        self.symbols = symbols_to_track

    async def stream_symbol(self, symbol: str):
        """Streams messages for a single symbol."""
        # This is a public but unofficial endpoint. Use with care.
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        
        try:
            response = await self.client.get(url, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            
            for message in data.get('messages', []):
                # We need a way to avoid processing the same message repeatedly.
                # A simple cache or checking the last seen message ID is needed.
                # For now, we'll process and publish.
                
                sentiment = message.get('entities', {}).get('sentiment', None)
                sentiment_label = sentiment.get('basic') if sentiment else 'NEUTRAL'

                post_data = {
                    "id": message['id'],
                    "symbol": symbol,
                    "text": message['body'],
                    "user": message['user']['username'],
                    "sentiment": sentiment_label # e.g., 'Bullish', 'Bearish'
                }
                await self.publish_to_redis('stocktwits_posts', post_data)
            
            logger.info(f"Fetched {len(data.get('messages', []))} messages for {symbol} from Stocktwits.")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching from Stocktwits for {symbol}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error streaming Stocktwits for {symbol}: {e}", exc_info=True)

    async def fetch_data(self):
        """Fetches data for all tracked symbols."""
        tasks = [self.stream_symbol(symbol) for symbol in self.symbols if "-USD" not in symbol]
        await asyncio.gather(*tasks)

