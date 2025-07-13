-- scripts/schema.sql
-- The complete SQL schema for the trading system's PostgreSQL database.
-- This should be run once to initialize the database.

-- Enable TimescaleDB extension if you have it installed (highly recommended for time-series data)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Table for storing historical price data
CREATE TABLE IF NOT EXISTS price_history (
    "timestamp" TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    volume BIGINT,
    PRIMARY KEY (symbol, "timestamp")
);

-- Convert the price_history table into a TimescaleDB hypertable for performance
-- SELECT create_hypertable('price_history', 'timestamp');

-- Table for storing generated trading signals
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    source_indicators JSONB, -- Use JSONB for better performance and indexing
    status VARCHAR(20) NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on symbol for faster lookups
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created_at ON signals (symbol, created_at DESC);

-- Table for storing executed trades
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id),
    symbol VARCHAR(16) NOT NULL,
    entry_price DOUBLE PRECISION NOT NULL,
    exit_price DOUBLE PRECISION,
    stop_loss DOUBLE PRECISION,
    position_size DOUBLE PRECISION NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'open', -- 'open', 'closed'
    pnl DOUBLE PRECISION,
    entry_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exit_timestamp TIMESTAMPTZ
);

-- Index on status and symbol for quickly finding open trades
CREATE INDEX IF NOT EXISTS idx_trades_status_symbol ON trades (status, symbol);

-- You can add more tables here for logging, performance metrics, etc.
```python