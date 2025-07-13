# src/main.py (FINAL REVISION)
# Main entry point for the autonomous trading system.

import asyncio
from config.settings import setup_logging, TRADING_MODE
from utils.logger import get_logger
import tweepy

# --- Import All Components ---
from execution.telegram_bot import TelegramBot
from data_ingestion.unusual_whales import UnusualWhalesIngester
from data_ingestion.bigshort import BigShortIngester
from data_ingestion.sec_edgar import SecEdgarIngester
from data_ingestion.news_rss import NewsRssIngester
from data_ingestion.yahoo_finance import YahooFinanceIngester
from data_ingestion.federal_reserve import FederalReserveIngester
from data_ingestion.twitter_api import TwitterIngester
from data_ingestion.reddit_scraper import RedditIngester
from data_ingestion.google_trends import GoogleTrendsIngester
from data_ingestion.stocktwits_scraper import StocktwitsIngester
from data_ingestion.alpha_vantage import AlphaVantageIngester
from data_ingestion.finviz_scraper import FinvizScraper
from ai_analysis.ensemble_manager import EnsembleManager
from signal_generation.signal_aggregator import SignalAggregator
from execution.paper_trader import PaperTrader
from risk_management.portfolio_monitor import PortfolioMonitor

setup_logging()
logger = get_logger(__name__)

class TradingSystem:
    def __init__(self):
        self.tasks = []
        self.components = []

        # --- Define Assets & Rules ---
        self.tracked_symbols = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "COIN", "MARA", "BTC-USD", "ETH-USD"]
        self.fred_series = ["DFF", "CPIAUCSL", "UNRATE"]
        self.twitter_rules = [tweepy.StreamRule(value=f"${s}") for s in self.tracked_symbols if "-USD" not in s]
        self.reddit_subreddits = ["wallstreetbets", "stocks", "investing"]
        self.google_keywords = self.tracked_symbols + ["interest rates", "inflation"]

        # --- Initialize All Components ---
        # Core Orchestrators and Executors
        self.telegram_bot = TelegramBot()
        self.ensemble_manager = EnsembleManager()
        self.signal_aggregator = SignalAggregator()
        self.portfolio_monitor = PortfolioMonitor()
        self.trade_executor = PaperTrader() if TRADING_MODE == 'paper' else self._handle_live_mode()

        # Data Ingesters (Paid and Free)
        self.components = [
            self.telegram_bot, self.ensemble_manager, self.signal_aggregator,
            self.portfolio_monitor, self.trade_executor,
            UnusualWhalesIngester(),
            BigShortIngester(),
            SecEdgarIngester(),
            YahooFinanceIngester(symbols_to_track=self.tracked_symbols),
            FederalReserveIngester(series_ids=self.fred_series),
            TwitterIngester(rules=self.twitter_rules),
            NewsRssIngester(feed_urls=["[http://feeds.reuters.com/reuters/businessNews](http://feeds.reuters.com/reuters/businessNews)"]),
            RedditIngester(subreddits=self.reddit_subreddits),
            GoogleTrendsIngester(keywords=self.google_keywords),
            StocktwitsIngester(symbols_to_track=self.tracked_symbols),
            AlphaVantageIngester(symbols_to_track=self.tracked_symbols),
            FinvizScraper(symbols_to_track=self.tracked_symbols)
        ]

    def _handle_live_mode(self):
        raise NotImplementedError("Live trading executor not implemented.")

    async def run(self):
        logger.info("Starting the autonomous trading system...")
        try:
            for component in self.components:
                self.tasks.append(asyncio.create_task(component.run()))
            logger.info(f"All {len(self.components)} services initialized. System is running in {TRADING_MODE} mode.")
            await asyncio.gather(*self.tasks)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Trading system shutting down.")
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info("Executing graceful shutdown...")
        for task in self.tasks:
            if not task.done(): task.cancel()
        for component in self.components:
            if hasattr(component, 'close') and asyncio.iscoroutinefunction(component.close):
                await component.close()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    system = TradingSystem()
    try:
        asyncio.run(system.run())
    except Exception as e:
        logger.critical(f"Failed to run the trading system: {e}", exc_info=True)
