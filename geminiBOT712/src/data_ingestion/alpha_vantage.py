# src/data_ingestion/alpha_vantage.py
# Data ingester for fundamental data from Alpha Vantage.

from .base_ingester import BaseIngester
from utils.logger import get_logger
from config.api_config import API_KEYS

logger = get_logger(__name__)

class AlphaVantageIngester(BaseIngester):
    """

    Fetches fundamental company data (e.g., P/E, EPS) from Alpha Vantage.
    """
    def __init__(self, symbols_to_track: list):
        api_key = API_KEYS.get("alpha_vantage")
        super().__init__(api_key=api_key, api_endpoint="[https://www.alphavantage.co/query](https://www.alphavantage.co/query)")
        self.symbols = symbols_to_track
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found. Ingester will be disabled.")

    async def fetch_symbol_overview(self, symbol: str):
        """Fetches the company overview data for a single symbol."""
        if not self.api_key: return

        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.api_key
        }
        try:
            response = await self.client.get(self.api_endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if "Note" in data: # Indicates API limit reached
                logger.warning(f"Alpha Vantage API limit likely reached: {data['Note']}")
                return
            
            if not data or 'Symbol' not in data:
                logger.warning(f"No fundamental data returned for {symbol} from Alpha Vantage.")
                return

            logger.info(f"Fetched fundamental data for {symbol}.")
            await self.publish_to_redis('fundamental_data', data)

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}", exc_info=True)

    async def fetch_data(self):
        """
        Fetches data for all symbols, respecting API rate limits.
        The free tier is 5 requests per minute.
        """
        for symbol in self.symbols:
            if "-USD" in symbol: continue # Skip crypto
            await self.fetch_symbol_overview(symbol)
            await asyncio.sleep(15) # Wait 15s between requests to stay under the limit
