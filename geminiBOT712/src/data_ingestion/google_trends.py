# src/data_ingestion/google_trends.py
# Data ingester for Google Trends data.

from .base_ingester import BaseIngester
from utils.logger import get_logger
from pytrends.request import TrendReq
import pandas as pd
import asyncio

logger = get_logger(__name__)

class GoogleTrendsIngester(BaseIngester):
    """
    Fetches interest over time data from Google Trends for a list of keywords.
    """
    def __init__(self, keywords: list):
        super().__init__()
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.keywords = keywords

    async def fetch_keyword(self, keyword: str):
        """Fetches interest over time for a single keyword."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self.pytrends.build_payload,
            [keyword],
            cat=0,
            timeframe='now 1-d',
            geo='',
            gprop=''
        )

        interest_df = await loop.run_in_executor(None, self.pytrends.interest_over_time)
        if interest_df.empty or keyword not in interest_df.columns:
            return

        latest_interest = interest_df[keyword].iloc[-1]
        logger.info(f"Google Trends interest for '{keyword}': {latest_interest}")
        trend_data = {"keyword": keyword, "interest": int(latest_interest)}
        await self.publish_to_redis('google_trends', trend_data)

    async def fetch_data(self):
        """Fetches interest data concurrently for all configured keywords."""
        try:
            tasks = [self.fetch_keyword(k) for k in self.keywords]
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error fetching Google Trends data: {e}", exc_info=True)

