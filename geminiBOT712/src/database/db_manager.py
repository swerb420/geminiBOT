# src/database/db_manager.py (REVISED)
# Asynchronous database manager for handling all DB operations.

import asyncpg
from config.settings import DATABASE_URL
from utils.logger import get_logger
import json
import pandas as pd

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
                self.pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=5, max_size=20)
                logger.info("Database connection pool created successfully.")
            except Exception as e:
                logger.critical(f"Failed to create database connection pool: {e}", exc_info=True)
                raise

    async def disconnect(self):
        """Closes the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed.")

    async def save_price_data(self, price_data: dict):
        """Saves a new price tick to a hypertable (if using TimescaleDB)."""
        # For TimescaleDB, you'd have a specific hypertable for price data.
        # For standard PostgreSQL, we'll insert into a regular table.
        query = """
            INSERT INTO price_history (symbol, timestamp, price, volume)
            VALUES ($1, to_timestamp($2), $3, $4)
            ON CONFLICT (symbol, timestamp) DO NOTHING;
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    price_data['symbol'],
                    price_data['regularMarketTime'],
                    price_data['regularMarketPrice'],
                    price_data.get('regularMarketVolume', 0)
                )
        except Exception as e:
            logger.error(f"Error saving price data for {price_data.get('symbol')}: {e}")


    async def get_historical_data(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Retrieves historical price data for a symbol and returns a DataFrame."""
        query = """
            SELECT timestamp, price as close, volume
            FROM price_history
            WHERE symbol = $1
            ORDER BY timestamp DESC
            LIMIT $2;
        """
        try:
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, symbol, limit)
            if not records:
                return pd.DataFrame()
            
            df = pd.DataFrame(records, columns=['timestamp', 'close', 'volume'])
            df = df.set_index('timestamp').sort_index()
            return df
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()

    async def save_signal(self, signal_data: dict) -> int:
        """Saves a generated signal to the database and returns its ID."""
        query = """
            INSERT INTO signals (symbol, direction, confidence_score, source_indicators, status)
            VALUES ($1, $2, $3, $4, 'generated') RETURNING id;
        """
        async with self.pool.acquire() as conn:
            signal_id = await conn.fetchval(query, signal_data['symbol'], signal_data['direction'],
                                            signal_data['confidence_score'], json.dumps(signal_data['source_indicators']))
        logger.info(f"Saved signal {signal_id} for {signal_data['symbol']} to database.")
        return signal_id

    async def save_trade(self, trade_data: dict) -> int:
        """Saves an executed trade to the database."""
        query = """
            INSERT INTO trades (signal_id, symbol, entry_price, stop_loss, position_size, status)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id;
        """
        async with self.pool.acquire() as conn:
            trade_id = await conn.fetchval(query, trade_data['signal_id'], trade_data['symbol'], trade_data['entry_price'],
                                           trade_data['stop_loss'], trade_data['position_size'], trade_data['status'])
        logger.info(f"Saved trade {trade_id} for {trade_data['symbol']} to database.")
        return trade_id

    async def get_open_trades(self) -> list:
        """Retrieves all trades with 'open' status."""
        query = "SELECT * FROM trades WHERE status = 'open';"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
        return [dict(row) for row in rows]

