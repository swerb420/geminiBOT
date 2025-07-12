# scripts/run_backtest.py
# Example script to run the backtesting engine on historical data.

import pandas as pd
import os
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.performance_analyzer import PerformanceAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)

def load_historical_data(file_path: str) -> pd.DataFrame:
    """
    Loads historical price data from a CSV file.
    Assumes CSV has 'Date', 'Open', 'High', 'Low', 'Close', 'Volume' columns.
    """
    if not os.path.exists(file_path):
        logger.error(f"Historical data file not found: {file_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
    # Ensure column names are lowercase for consistency
    df.columns = [col.lower() for col in df.columns]
    logger.info(f"Loaded {len(df)} rows of historical data from {file_path}")
    return df

def main():
    """
    Main function to set up and run the backtest.
    """
    logger.info("Setting up backtest...")
    
    # --- Configuration ---
    initial_capital = 100000 # $100,000
    # You need to provide your own historical data file in CSV format.
    # You can download this from sources like Yahoo Finance.
    data_file = "data/historical/AAPL_1Y.csv" 

    # --- Load Data ---
    historical_prices = load_historical_data(data_file)
    if historical_prices.empty:
        logger.critical("Cannot run backtest without historical data. Exiting.")
        return

    data_dict = {"AAPL": historical_prices}

    # --- Run Backtest ---
    engine = BacktestEngine(historical_data=data_dict, capital=initial_capital)
    trades, equity_curve = engine.run()

    # --- Analyze Performance ---
    if not trades:
        logger.warning("No trades were executed during the backtest.")
        return
        
    analyzer = PerformanceAnalyzer(trades=trades, equity_curve=equity_curve)
    analyzer.print_report()

    # --- Optional: Save results ---
    # equity_curve.to_csv("results/equity_curve.csv")
    # pd.DataFrame(trades).to_csv("results/trades.csv")
    logger.info("Backtest script finished.")


if __name__ == "__main__":
    # Create dummy data directories if they don't exist
    os.makedirs("data/historical", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # You would need to place your actual data file in 'data/historical/'
    # For demonstration, we'll skip running main() if the file doesn't exist.
    if os.path.exists("data/historical/AAPL_1Y.csv"):
        main()
    else:
        logger.warning("Dummy data file 'data/historical/AAPL_1Y.csv' not found.")
        logger.warning("Please download historical data and place it there to run the backtest.")

