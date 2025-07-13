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

    async def fetch_data(self):
        """
        Fetches interest over time for the configured keywords.
        Note: The pytrends library is synchronous, so we run it in an executor
        to avoid blocking the asyncio event loop.
        """
        loop = asyncio.get_running_loop()
        
        try:
            # Build the payload
            await loop.run_in_executor(
                None, 
                self.pytrends.build_payload, 
                self.keywords, 
                cat=0, 
                timeframe='now 1-d', # Interest over the last day
                geo='', 
                gprop=''
            )
            
            # Get interest over time
            interest_df = await loop.run_in_executor(None, self.pytrends.interest_over_time)
            
            if interest_df.empty:
                logger.info("No new Google Trends data.")
                return

            for keyword in self.keywords:
                if keyword in interest_df.columns:
                    latest_interest = interest_df[keyword].iloc[-1]
                    logger.info(f"Google Trends interest for '{keyword}': {latest_interest}")
                    trend_data = {"keyword": keyword, "interest": int(latest_interest)}
                    await self.publish_to_redis('google_trends', trend_data)

        except Exception as e:
            # The Google Trends API can be sensitive to too many requests
            logger.error(f"Error fetching Google Trends data: {e}", exc_info=True)

