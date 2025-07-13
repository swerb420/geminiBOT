# scripts/initialize_db.py
# A Python script to execute the schema.sql file against the database.

import asyncpg
import asyncio
import os
from src.config.settings import DATABASE_URL
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    logger.info("Connecting to the database to initialize schema...")
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if not os.path.exists(schema_path):
            logger.critical(f"Schema file not found at {schema_path}")
            return
            
        logger.info(f"Reading schema from {schema_path}...")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        logger.info("Executing schema setup script...")
        await conn.execute(schema_sql)
        logger.info("Database schema initialized successfully!")

    except Exception as e:
        logger.critical(f"An error occurred during database initialization: {e}", exc_info=True)
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    # This allows running the script directly: `python scripts/initialize_db.py`
    asyncio.run(main())
