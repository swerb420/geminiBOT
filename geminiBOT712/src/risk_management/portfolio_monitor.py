# src/risk_management/portfolio_monitor.py
# Tracks open positions, portfolio value, and enforces risk limits.

import asyncio
from utils.logger import get_logger
from database.db_manager import DBManager
from config.trading_config import MAX_DAILY_LOSS_LIMIT

logger = get_logger(__name__)

class PortfolioMonitor:
    """
    Monitors the overall portfolio in real-time.
    - Tracks open positions and calculates current P&L.
    - Enforces daily loss limits (circuit breaker).
    - Provides portfolio health status.
    """
    def __init__(self, portfolio_capital=10000):
        self.db_manager = DBManager()
        self.capital = portfolio_capital
        self.is_trading_halted = False

    async def run(self, interval_seconds: int = 15):
        """Runs the monitoring loop at a specified interval."""
        logger.info(f"PortfolioMonitor started. Checking portfolio every {interval_seconds}s.")
        await self.db_manager.connect()
        while True:
            try:
                if self.is_trading_halted:
                    logger.warning("TRADING HALTED due to risk limit breach. No new trades will be placed.")
                    await asyncio.sleep(300) # Check less frequently when halted
                    continue
                
                await self.check_portfolio_pnl()

            except Exception as e:
                logger.error(f"Error in PortfolioMonitor loop: {e}", exc_info=True)
            await asyncio.sleep(interval_seconds)

    async def check_portfolio_pnl(self):
        """
        Fetches all open trades, calculates their current P&L, and checks against
        the daily loss limit.
        """
        open_trades = await self.db_manager.get_open_trades()
        if not open_trades:
            return

        total_pnl = 0.0
        for trade in open_trades:
            # This requires a live price feed. For now, we simulate this.
            # In a real system, this would use the same price source as the executor.
            current_price = await self.get_current_price(trade['symbol'])
            if current_price is None:
                continue

            direction_multiplier = 1 if trade['direction'] == 'BULLISH' else -1
            pnl = (current_price - trade['entry_price']) * trade['position_size'] * direction_multiplier
            total_pnl += pnl
        
        daily_drawdown = -total_pnl / self.capital
        logger.info(f"Current P&L for open positions: ${total_pnl:.2f}. Daily Drawdown: {daily_drawdown:.2%}")

        # --- Circuit Breaker Logic ---
        if daily_drawdown >= MAX_DAILY_LOSS_LIMIT:
            logger.critical("!!! MAX DAILY LOSS LIMIT REACHED !!!")
            logger.critical("--- HALTING ALL TRADING FOR THE DAY ---")
            self.is_trading_halted = True
            # Here you would also send an urgent alert via Telegram
            # await telegram_bot.send_alert("CRITICAL: MAX DAILY LOSS LIMIT REACHED. TRADING HALTED.")

    async def get_current_price(self, symbol: str) -> float | None:
        # This would be connected to the live price feed from Redis
        # This is a placeholder for demonstration
        # In the final system, it will be integrated with the redis price_updates channel
        return None # Needs to be implemented

    async def close(self):
        await self.db_manager.disconnect()
