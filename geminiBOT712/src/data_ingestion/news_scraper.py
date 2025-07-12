# src/data_ingestion/news_scraper.py
# Scrapes headlines directly from a financial news website.

from .base_ingester import BaseIngester
from utils.logger import get_logger
import httpx
from bs4 import BeautifulSoup
import json

logger = get_logger(__name__)


class FinancialNewsScraper(BaseIngester):
    """
    Scrapes the headlines from a major financial news site's homepage.
    This provides a free, real-time source of news for sentiment analysis.
    """

    def __init__(self, news_url: str = "https://www.marketwatch.com/"):
        super().__init__()
        self.news_url = news_url
        self.seen_headlines = set()  # Avoid processing duplicate headlines

    async def fetch_data(self):
        """Scrapes the news website for the latest headlines."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            delay = 1.0
            for attempt in range(1, 4):
                try:
                    async with httpx.AsyncClient(
                        headers=headers, timeout=30.0, follow_redirects=True
                    ) as client:
                        response = await client.get(self.news_url)
                        response.raise_for_status()
                    break
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(
                        f"Attempt {attempt} failed fetching news: {e}", exc_info=True
                    )
                    if attempt == 3:
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2

            soup = BeautifulSoup(response.text, "html.parser")

            # The specific tags and classes will change depending on the site.
            # This is an example for MarketWatch and needs to be maintained.
            headlines = soup.find_all("h3", class_="article__headline")

            new_headlines_found = 0
            for headline in headlines:
                title = headline.get_text(strip=True)
                link_tag = headline.find("a", class_="link")
                link = link_tag["href"] if link_tag else None

                if title and link and title not in self.seen_headlines:
                    self.seen_headlines.add(title)
                    new_headlines_found += 1

                    # Extract potential symbols from the headline text
                    symbols = [
                        word.replace("$", "")
                        for word in title.split()
                        if word.startswith("$")
                    ]

                    news_data = {
                        "source": "MarketWatch Scraper",
                        "title": title,
                        "link": link,
                        "symbols": symbols,
                    }
                    await self.publish_to_redis("news_articles", news_data)

            if new_headlines_found > 0:
                logger.info(
                    f"Scraped {new_headlines_found} new headlines from {self.news_url}"
                )

        except Exception as e:
            logger.error(
                f"Error scraping financial news from {self.news_url}: {e}",
                exc_info=True,
            )
