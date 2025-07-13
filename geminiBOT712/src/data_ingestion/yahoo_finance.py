# src/data_ingestion/yahoo_finance.py
# Data ingester for real-time quotes from Yahoo Finance.

from .base_ingester import BaseIngester
from config.api_config import API_ENDPOINTS
from utils.logger import get_logger
import json

logger = get_logger(__name__)

class YahooFinanceIngester(BaseIngester):
    """
    Fetches real-time price quotes for a list of tracked symbols
    from Yahoo Finance and publishes them to Redis.
    """
    def __init__(self, symbols_to_track: list):
        """
        Args:
            symbols_to_track (list): A list of stock/crypto tickers to get quotes for.
        """
        super().__init__(api_endpoint=API_ENDPOINTS.get("yahoo_finance"))
        if not symbols_to_track:
            raise ValueError("YahooFinanceIngester requires a list of symbols to track.")
        self.symbols = symbols_to_track

    async def fetch_data(self):
        """
        Fetches the latest quotes for all tracked symbols.
        """
        # Yahoo Finance API can take multiple symbols separated by commas
        symbols_str = ",".join(self.symbols)
        # Using v7 for detailed quote information
        url = f"{self.api_endpoint}v7/finance/quote"
        params = {'symbols': symbols_str}
        
        # Yahoo Finance can be picky about headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            quote_response = response.json().get('quoteResponse', {})
            results = quote_response.get('result', [])

            if not results:
                logger.warning(f"Could not fetch quotes for symbols: {symbols_str}")
                return

            for quote in results:
                # Publish each quote to the price updates channel
                await self.publish_to_redis('price_updates', quote)
            
            logger.info(f"Fetched and published quotes for {len(results)} symbols.")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching from Yahoo Finance: {e.response.status_code}")
        except Exception as e:
            logger.error(f"An error occurred while fetching from Yahoo Finance: {e}", exc_info=True)
