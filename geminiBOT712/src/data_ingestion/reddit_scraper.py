# src/data_ingestion/reddit_scraper.py
# Data ingester for Reddit, specifically for subreddits like r/wallstreetbets.

from .base_ingester import BaseIngester
from utils.logger import get_logger
import asyncpraw # The asynchronous version of the Python Reddit API Wrapper

# NOTE: You will need to create a script app on your Reddit account
# to get these credentials.
from config.api_config import API_KEYS

logger = get_logger(__name__)

class RedditIngester(BaseIngester):
    """
    Streams new submissions and comments from specified subreddits.
    """
    def __init__(self, subreddits: list):
        super().__init__()
        self.reddit_keys = API_KEYS.get("reddit", {})
        if not all(self.reddit_keys.values()):
            logger.warning("Reddit API credentials not found. Ingester will be disabled.")
            self.reddit = None
            return
        
        self.reddit = asyncpraw.Reddit(
            client_id=self.reddit_keys['client_id'],
            client_secret=self.reddit_keys['client_secret'],
            user_agent=self.reddit_keys['user_agent']
        )
        self.subreddits_str = "+".join(subreddits)

    async def stream_submissions(self):
        """Streams new posts from the specified subreddits."""
        if not self.reddit: return
        try:
            subreddit = await self.reddit.subreddit(self.subreddits_str)
            logger.info(f"Streaming new submissions from r/{self.subreddits_str}...")
            async for submission in subreddit.stream.submissions(skip_existing=True):
                logger.info(f"New WSB Post: {submission.title}")
                post_data = {"id": submission.id, "title": submission.title, "text": submission.selftext, "type": "submission"}
                await self.publish_to_redis('reddit_posts', post_data)
        except Exception as e:
            logger.error(f"Error in Reddit submission stream: {e}", exc_info=True)
            await asyncio.sleep(60) # Wait before retrying
            await self.stream_submissions()


    async def run(self, interval_seconds: int = 0):
        # This is a streaming ingester, so the interval isn't used.
        await self.stream_submissions()

    async def close(self):
        if self.reddit:
            await self.reddit.close()
```python
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

