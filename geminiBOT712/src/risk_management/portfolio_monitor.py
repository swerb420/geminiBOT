# src/risk_management/portfolio_monitor.py (REVISED)
# Tracks open positions, enforces risk limits, and closes trades.

import asyncio
from utils.logger import get_logger
from database.db_manager import DBManager
from config.trading_config import MAX_DAILY_LOSS_LIMIT
from risk_management.volatility_manager import VolatilityManager
import redis.asyncio as redis
import json

logger = get_logger(__name__)

class PortfolioMonitor:
    """
    Monitors the overall portfolio, manages open trades by checking stop losses,
    and triggers the signal performance feedback loop upon closing a trade.
    """
    def __init__(self, portfolio_capital=10000):
        self.db_manager = DBManager()
        self.redis_client = redis.Redis(decode_responses=True)
        self.capital = portfolio_capital
        self.is_trading_halted = False
        self.vol_manager = VolatilityManager()

    async def run(self, interval_seconds: int = 5): # Check more frequently
        logger.info("PortfolioMonitor started. Checking positions every 5s.")
        await self.db_manager.connect()
        while True:
            try:
                if self.is_trading_halted:
                    # ... (halt logic) ...
                    continue
                
                await self.check_open_positions()

            except Exception as e:
                logger.error(f"Error in PortfolioMonitor loop: {e}", exc_info=True)
            await asyncio.sleep(interval_seconds)

    async def check_open_positions(self):
        """
        Fetches all open trades and checks if their stop loss has been hit.
        """
        open_trades = await self.db_manager.get_open_trades()
        if not open_trades:
            return

        for trade in open_trades:
            current_price = await self.get_current_price(trade['symbol'])
            if current_price is None:
                continue

            # Update trailing stop based on latest volatility
            price_history = await self.db_manager.get_historical_data(trade['symbol'])
            atr = self.vol_manager.calculate_atr(price_history) if not price_history.empty else 0
            direction_label = 'BULLISH' if trade['entry_price'] < trade['stop_loss'] else 'BEARISH'
            new_stop = self.vol_manager.trailing_stop(current_price, trade['stop_loss'], direction_label, atr)
            if new_stop != trade['stop_loss']:
                await self.db_manager.update_trade_stop(trade['id'], new_stop)
                trade['stop_loss'] = new_stop

            # Check stop loss
            direction = 1 if trade['entry_price'] < trade['stop_loss'] else -1 # Determine direction from SL
            if (direction == 1 and current_price >= trade['stop_loss']) or \
               (direction == -1 and current_price <= trade['stop_loss']):
                logger.warning(f"STOP LOSS HIT for {trade['symbol']} at price {current_price:.2f}")
                await self.close_position(trade, trade['stop_loss']) # Close at the stop price

    async def close_position(self, trade: dict, exit_price: float):
        """Closes a position and updates the signal feedback loop."""
        closed_trade_details = await self.db_manager.close_trade(trade['id'], exit_price)
        if not closed_trade_details:
            return

        # Calculate P&L
        direction_multiplier = 1 if closed_trade_details['entry_price'] < closed_trade_details['stop_loss'] else -1
        pnl = (exit_price - closed_trade_details['entry_price']) * closed_trade_details['position_size'] * direction_multiplier
        
        # Trigger the feedback loop!
        await self.db_manager.update_signal_outcome(closed_trade_details['signal_id'], pnl)
        
        # You would also send a Telegram alert here about the closed trade.

    async def get_current_price(self, symbol: str) -> float | None:
        price_data_json = await self.redis_client.get(f"price:{symbol}")
        if not price_data_json: return None
        return json.loads(price_data_json).get('regularMarketPrice')

    async def close(self):
        await self.db_manager.disconnect()
