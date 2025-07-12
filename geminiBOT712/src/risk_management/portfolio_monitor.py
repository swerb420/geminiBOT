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
```python
# src/database/db_manager.py
# Asynchronous database manager for handling all DB operations.

import asyncpg
from config.settings import DATABASE_URL
from utils.logger import get_logger
from .models import Signal, Trade # Assuming models are defined elsewhere

logger = get_logger(__name__)

class DBManager:
    """
    Provides a clean, async interface for all database operations.
    Uses a connection pool for efficient database access.
    """
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Creates the database connection pool."""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(DATABASE_URL)
                logger.info("Database connection pool created successfully.")
            except Exception as e:
                logger.critical(f"Failed to create database connection pool: {e}", exc_info=True)
                raise

    async def disconnect(self):
        """Closes the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed.")

    async def save_signal(self, signal_data: dict) -> int:
        """Saves a generated signal to the database and returns its ID."""
        query = """
            INSERT INTO signals (symbol, direction, confidence_score, source_indicators, status)
            VALUES ($1, $2, $3, $4, 'generated')
            RETURNING id;
        """
        async with self.pool.acquire() as conn:
            signal_id = await conn.fetchval(
                query,
                signal_data['symbol'],
                signal_data['direction'],
                signal_data['confidence_score'],
                json.dumps(signal_data['source_indicators'])
            )
        logger.info(f"Saved signal {signal_id} for {signal_data['symbol']} to database.")
        return signal_id

    async def save_trade(self, trade_data: dict) -> int:
        """Saves an executed trade to the database."""
        query = """
            INSERT INTO trades (signal_id, symbol, entry_price, stop_loss, position_size, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id;
        """
        async with self.pool.acquire() as conn:
            trade_id = await conn.fetchval(
                query,
                trade_data['signal_id'],
                trade_data['symbol'],
                trade_data['entry_price'],
                trade_data['stop_loss'],
                trade_data['position_size'],
                trade_data['status']
            )
        logger.info(f"Saved trade {trade_id} for {trade_data['symbol']} to database.")
        return trade_id

    async def get_open_trades(self) -> list:
        """Retrieves all trades with 'open' status."""
        query = "SELECT * FROM trades WHERE status = 'open';"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
        return [dict(row) for row in rows]

