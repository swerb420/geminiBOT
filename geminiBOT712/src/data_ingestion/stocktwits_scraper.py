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

```python
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
```python
# src/data_ingestion/finviz_scraper.py
# Scrapes analyst ratings and price targets from Finviz.

from .base_ingester import BaseIngester
from utils.logger import get_logger
import httpx
from bs4 import BeautifulSoup
import json

logger = get_logger(__name__)

class FinvizScraper(BaseIngester):
    """
    Scrapes a symbol's Finviz page to extract analyst ratings.
    NOTE: Web scraping is fragile and can break if the website structure changes.
    """
    def __init__(self, symbols_to_track: list):
        super().__init__()
        self.symbols = symbols_to_track

    async def scrape_symbol(self, symbol: str):
        """Scrapes the Finviz page for a given symbol."""
        url = f"https://finviz.com/quote.ashx?t={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the analyst ratings table
                ratings_table = soup.find('table', class_='fullview-ratings-outer')
                if not ratings_table:
                    logger.info(f"No analyst ratings table found for {symbol} on Finviz.")
                    return

                latest_ratings = []
                for row in ratings_table.find_all('tr')[:5]: # Get latest 5 ratings
                    cols = row.find_all('td')
                    if len(cols) == 5:
                        rating = {
                            "date": cols[0].text,
                            "action": cols[1].text, # e.g., 'Upgrade', 'Reiterated'
                            "analyst": cols[2].text,
                            "rating": cols[3].text, # e.g., 'Buy', 'Outperform'
                            "price_target": cols[4].text
                        }
                        latest_ratings.append(rating)
                
                if latest_ratings:
                    logger.info(f"Scraped {len(latest_ratings)} analyst ratings for {symbol}.")
                    await self.publish_to_redis('analyst_ratings', {"symbol": symbol, "ratings": latest_ratings})

        except Exception as e:
            logger.error(f"Error scraping Finviz for {symbol}: {e}", exc_info=True)


    async def fetch_data(self):
        """Scrapes data for all tracked symbols."""
        tasks = [self.scrape_symbol(symbol) for symbol in self.symbols if "-USD" not in symbol]
        await asyncio.gather(*tasks)
