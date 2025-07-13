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
