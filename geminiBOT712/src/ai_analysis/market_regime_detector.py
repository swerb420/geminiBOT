# src/ai_analysis/market_regime_detector.py
# Analyzes overall market health to determine the current trading regime.

from utils.logger import get_logger
import pandas as pd
from database.db_manager import DBManager

logger = get_logger(__name__)

class MarketRegimeDetector:
    """
    Analyzes a market index (e.g., SPY) to classify the current
    market regime, providing crucial context for trading decisions.
    """
    def __init__(self, market_index_symbol='SPY'):
        self.market_index = market_index_symbol
        self.db_manager = DBManager()

    async def get_current_regime(self) -> str:
        """
        Determines the current market regime.

        Returns:
            A string representing the regime: 'BULLISH', 'BEARISH', 'SIDEWAYS', 'VOLATILE'.
        """
        # Fetch the last ~3 months of daily data for the market index
        price_history = await self.db_manager.get_historical_data(self.market_index, limit=90)
        if len(price_history) < 50:
            logger.warning(f"Not enough historical data for {self.market_index} to determine market regime.")
            return 'UNKNOWN'

        # --- Regime Logic ---
        # 1. Trend Detection (using moving averages)
        sma_20 = price_history['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = price_history['close'].rolling(window=50).mean().iloc[-1]
        
        # 2. Volatility Detection (using Bollinger Bands width)
        rolling_std = price_history['close'].rolling(window=20).std().iloc[-1]
        bollinger_width = (4 * rolling_std) / sma_20

        # --- Classification ---
        if bollinger_width > 0.15: # If band width is > 15% of the price, it's highly volatile
            return 'VOLATILE'
        elif sma_20 > sma_50 and price_history['close'].iloc[-1] > sma_20:
            return 'BULLISH'
        elif sma_20 < sma_50 and price_history['close'].iloc[-1] < sma_20:
            return 'BEARISH'
        else:
            return 'SIDEWAYS'

    async def run(self, redis_client):
        """Periodically checks the regime and caches it in Redis."""
        await self.db_manager.connect()
        while True:
            try:
                regime = await self.get_current_regime()
                logger.info(f"Current Market Regime detected: {regime}")
                await redis_client.set("insight:market:regime", regime, ex=3600) # Cache for 1 hour
            except Exception as e:
                logger.error(f"Error in MarketRegimeDetector loop: {e}")
            await asyncio.sleep(1800) # Check every 30 minutes
