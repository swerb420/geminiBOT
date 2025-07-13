# scripts/backfill_data.py
# Downloads free historical data and populates the database.

import yfinance as yf
import asyncio
from src.database.db_manager import DBManager
from src.utils.logger import get_logger
from datetime import datetime
import pandas as pd

logger = get_logger(__name__)

async def download_symbol_data(symbol: str) -> pd.DataFrame:
    """Downloads and returns historical data for a single symbol."""
    try:
        logger.info(f"Downloading hourly data for {symbol}...")
        # yfinance max period for 1h data is 730d
        data = await asyncio.to_thread(yf.download, symbol, period="730d", interval="1h")
        if data.empty:
            logger.warning(f"No hourly data returned for {symbol}.")
            return pd.DataFrame()
        
        # Prepare data for insertion
        data.reset_index(inplace=True)
        data.rename(columns={
            "Datetime": "timestamp", "Date": "timestamp", # yfinance uses different names
            "Open": "open", "High": "high", "Low": "low", 
            "Close": "close", "Volume": "volume"
        }, inplace=True)
        data['symbol'] = symbol
        return data[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        logger.error(f"Failed to download data for {symbol}: {e}")
        return pd.DataFrame()


async def run_backfill():
    """
    Downloads HOURLY OHLCV data for all tracked assets concurrently
    and uses a high-efficiency bulk insert to save it to the database.
    """
    db = DBManager()
    await db.connect()
    
    symbols_to_backfill = await db.get_tracked_assets()
    if not symbols_to_backfill:
        logger.warning("No tracked assets found in the database. Add assets via Telegram first.")
        await db.disconnect()
        return

    logger.info(f"Starting concurrent high-resolution data backfill for {len(symbols_to_backfill)} symbols...")
    
    # Run all downloads concurrently
    tasks = [download_symbol_data(symbol) for symbol in symbols_to_backfill]
    results = await asyncio.gather(*tasks)
    
    # Combine all dataframes and prepare for bulk insert
    all_data = pd.concat(results, ignore_index=True)
    all_data.dropna(inplace=True)
    
    if all_data.empty:
        logger.error("No data was successfully downloaded. Aborting database insert.")
        await db.disconnect()
        return

    logger.info(f"Total of {len(all_data)} data points to be saved to the database...")
    
    # Convert DataFrame to list of dicts for the bulk save method
    records = all_data.to_dict('records')
    await db.bulk_save_price_data(records)
            
    logger.info("Historical data backfill process complete.")
    await db.disconnect()

if __name__ == "__main__":
    # Ensure you have pandas-ta installed: pip install pandas-ta
    # This script should be run once to populate your database.
    asyncio.run(run_backfill())
```python