from .trade_executor import BaseTradeExecutor
from utils.logger import get_logger
from risk_management.volatility_manager import VolatilityManager
import json

logger = get_logger(__name__)

class PaperTrader(BaseTradeExecutor):
    """Simplified paper trading executor."""
    def __init__(self, portfolio_capital: float = 10000):
        super().__init__(portfolio_capital)
        self.volatility_manager = VolatilityManager()

    async def process_signal(self, signal: dict):
        symbol = signal['symbol']
        price = await self.get_current_price(symbol)
        if price is None:
            logger.warning(f"No price for {symbol}")
            return
        stop = price - 1 if signal['direction'] == 'BEARISH' else price + 1
        size = self.position_sizer.calculate_size(entry_price=price, stop_loss_price=stop)
        trade = {
            "signal_id": await self.db_manager.save_signal(signal),
            "symbol": symbol,
            "entry_price": price,
            "stop_loss": stop,
            "position_size": size,
            "status": "open",
        }
        await self.place_trade(trade)

    async def place_trade(self, trade: dict):
        logger.info(f"Simulated trade: {trade}")
        await self.db_manager.save_trade(trade)

    async def get_current_price(self, symbol: str) -> float | None:
        key = f"price:{symbol}"
        data = await self.redis_client.get(key)
        if not data:
            return None
        return json.loads(data).get('regularMarketPrice')
