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
