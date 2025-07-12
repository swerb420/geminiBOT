# src/execution/live_broker.py
# Framework for a live trade executor connecting to a real broker API.

from .trade_executor import BaseTradeExecutor
from utils.logger import get_logger
# import alpaca_trade_api as tradeapi # Example for Alpaca

logger = get_logger(__name__)

class LiveBroker(BaseTradeExecutor):
    """
    Implements the trade executor for a live brokerage account.
    This is a framework and requires a specific broker API implementation.
    """
    def __init__(self, portfolio_capital=10000):
        super().__init__(portfolio_capital)
        # --- Broker API Connection ---
        # self.api = tradeapi.REST(API_KEY, SECRET_KEY, base_url='[https://paper-api.alpaca.markets](https://paper-api.alpaca.markets)')
        # account = self.api.get_account()
        # logger.info(f"Connected to live broker. Account status: {account.status}")
        logger.warning("LiveBroker is a framework. You must implement the connection to your broker's API.")

    async def place_trade(self, signal: dict, signal_id: int, entry_price: float, stop_loss: float, size: float):
        """
        Places a live trade order through the broker's API.
        """
        symbol = signal['symbol']
        direction = 'buy' if signal['direction'] == 'BULLISH' else 'sell'
        
        logger.critical(f"--- PLACING LIVE TRADE ---")
        logger.critical(f"Symbol: {symbol}, Direction: {direction}, Size: {size}")
        
        try:
            # --- Example API call for a bracket order (entry, take profit, stop loss) ---
            # self.api.submit_order(
            #     symbol=symbol,
            #     qty=size,
            #     side=direction,
            #     type='market',
            #     time_in_force='day',
            #     order_class='bracket',
            #     stop_loss={'stop_price': stop_loss},
            #     take_profit={'limit_price': entry_price + (entry_price - stop_loss) * 2} # Example 2:1 R/R
            # )
            logger.info(f"Live order for {symbol} submitted successfully.")
            
            # Save the executed trade to the database
            trade_details = {"signal_id": signal_id, "symbol": symbol, "entry_price": entry_price,
                             "stop_loss": stop_loss, "position_size": size, "status": "open"}
            await self.db_manager.save_trade(trade_details)

        except Exception as e:
            logger.error(f"Failed to place live order for {symbol}: {e}", exc_info=True)
            # You might want to send a Telegram alert here

    async def get_current_price(self, symbol: str) -> float | None:
        """Retrieves the latest price for a symbol directly from the broker."""
        try:
            # return self.api.get_latest_trade(symbol).price
            return await super().get_current_price(symbol) # Fallback to Redis cache
        except Exception as e:
            logger.error(f"Could not get live price from broker for {symbol}: {e}")
            return await super().get_current_price(symbol) # Fallback to Redis cache
```python
# src/execution/paper_trader.py (REVISED)
# A simulated trade executor for paper trading.

from .trade_executor import BaseTradeExecutor
from utils.logger import get_logger
from risk_management.volatility_manager import VolatilityManager
import json

logger = get_logger(__name__)

class PaperTrader(BaseTradeExecutor):
    """
    Implements the trade executor for a simulated paper trading account.
    Now uses the VolatilityManager for dynamic stop losses.
    """
    def __init__(self, portfolio_capital=10000):
        super().__init__(portfolio_capital)
        self.volatility_manager = VolatilityManager()

    async def process_signal(self, signal: dict):
        """
        Processes a raw signal, using volatility-adjusted risk params.
        """
        symbol = signal['symbol']
        current_price = await self.get_current_price(symbol)
        if not current_price:
            logger.warning(f"Could not get current price for {symbol}. Skipping signal.")
            return

        # Fetch historical data to calculate ATR
        price_history = await self.db_manager.get_historical_data(symbol)
        if price_history.empty:
            logger.warning(f"No historical data for {symbol} to calculate ATR. Using fixed stop.")
            atr = 0
        else:
            atr = self.volatility_manager.calculate_atr(price_history)

        # Calculate a dynamic, volatility-adjusted stop loss
        stop_loss_price = self.volatility_manager.get_volatility_adjusted_stop_loss(
            entry_price=current_price,
            direction=signal['direction'],
            atr=atr,
            multiplier=2.0 # 2x ATR stop loss
        )
        
        size = self.position_sizer.calculate_size(entry_price=current_price, stop_loss_price=stop_loss_price)
        if size <= 0:
            logger.warning(f"Calculated position size is zero for {symbol}. Skipping trade.")
            return
            
        signal_id = await self.db_manager.save_signal(signal)
        await self.place_trade(signal, signal_id, current_price, stop_loss_price, size)

    async def place_trade(self, signal: dict, signal_id: int, entry_price: float, stop_loss: float, size: float):
        """Simulates placing a trade by logging and saving it."""
        trade_details = {"signal_id": signal_id, "symbol": signal['symbol'], "entry_price": entry_price,
                         "stop_loss": stop_loss, "position_size": size, "status": "open"}
        logger.critical(f"--- PAPER TRADE EXECUTED (DYNAMIC RISK) ---")
        logger.critical(f"Symbol: {signal['symbol']}, Direction: {signal['direction']}, Entry: {entry_rice:.2f}, Size: {size:.4f}, Stop: {stop_loss:.2f}")
        await self.db_manager.save_trade(trade_details)

    async def get_current_price(self, symbol: str) -> float | None:
        price_key = f"price:{symbol}"
        price_data_json = await self.redis_client.get(price_key)
        if not price_data_json:
            logger.warning(f"No price data found in Redis for symbol: {symbol}")
            return None
        price_data = json.loads(price_data_json)
        return price_data.get('regularMarketPrice')
```python
# src/ai_analysis/ensemble_manager.py (REVISED)
# The central nervous system of the AI pipeline.

import asyncio
import json
import redis.asyncio as redis
from config.settings import REDIS_HOST, REDIS_PORT
from utils.logger import get_logger
from ai_analysis.sentiment_analyzer import SentimentAnalyzer
from ai_analysis.pattern_matcher import PatternMatcher
from ai_analysis.correlation_analyzer import CorrelationAnalyzer
from ai_analysis.fed_predictor import FedPredictor
from ai_analysis.earnings_predictor import EarningsPredictor
from signal_generation.flow_momentum import FlowMomentumAlgorithm
from database.db_manager import DBManager # Import DBManager
import pandas as pd

logger = get_logger(__name__)

class EnsembleManager:
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.db_manager = DBManager() # Instantiate DBManager
        
        # ... (rest of the initializers) ...
        self.sentiment_analyzer = SentimentAnalyzer()
        self.pattern_matcher = PatternMatcher()
        self.fed_predictor = FedPredictor()
        # ...

    async def run(self):
        """Connects to DB then starts listening."""
        await self.db_manager.connect()
        await self.listen()

    async def close(self):
        """Closes DB connection on shutdown."""
        await self.db_manager.disconnect()

    # ... (listen method remains the same) ...

    async def process_price_update(self, price_data: dict):
        """
        On a new price update, fetch historical data from the DB
        and run pattern matching.
        """
        symbol = price_data.get('symbol')
        if not symbol: return

        # Save the latest price tick to the database for history
        await self.db_manager.save_price_data(price_data)

        # Now fetch the updated history from the database
        history_df = await self.db_manager.get_historical_data(symbol, limit=200)
        if history_df.empty: return

        patterns = self.pattern_matcher.analyze(history_df)
        if patterns:
            await self.store_insight(symbol, 'chart_patterns', patterns, 3600)

    # ... (other processor methods remain the same) ...

    # We can now remove the placeholder get_historical_data method
