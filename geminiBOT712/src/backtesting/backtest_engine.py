# src/backtesting/backtest_engine.py
# An event-driven backtesting engine to simulate trading strategies.

import pandas as pd
from utils.logger import get_logger
from ai_analysis.sentiment_analyzer import SentimentAnalyzer # Example analyzer
from signal_generation.flow_momentum import FlowMomentumAlgorithm # Example algorithm
from risk_management.position_sizer import PositionSizer

logger = get_logger(__name__)

class BacktestEngine:
    """
    Simulates the trading system's logic on historical data.
    It processes data point by point, simulating the passage of time.
    """
    def __init__(self, historical_data: dict, capital=10000):
        """
        Args:
            historical_data (dict): A dictionary where keys are symbols and
                                    values are pandas DataFrames of their price history.
            capital (int): The starting capital for the backtest.
        """
        self.historical_data = historical_data
        self.capital = capital
        self.equity_curve = []
        self.trades = []
        
        # Initialize components needed for the simulation
        self.position_sizer = PositionSizer(total_capital=self.capital)
        # In a real backtest, you would use simulated or historical versions of these
        # self.sentiment_analyzer = SentimentAnalyzer()
        # self.flow_momentum_analyzer = FlowMomentumAlgorithm()

    def run(self):
        """
        Runs the backtest simulation.
        This is a simplified example. A full event-driven backtester would merge
        all data sources (prices, news, flow) into a single chronological event stream.
        """
        logger.info(f"Starting backtest with initial capital ${self.capital:,.2f}")
        
        # For this example, we'll iterate through the price data of a single asset
        # A multi-asset backtest is significantly more complex.
        main_symbol = list(self.historical_data.keys())[0]
        data = self.historical_data[main_symbol]
        
        open_position = None

        for i, row in data.iterrows():
            current_price = row['close']
            
            # --- Portfolio Management ---
            if open_position:
                # Check for stop-loss or take-profit
                if open_position['direction'] == 'LONG' and current_price <= open_position['stop_loss']:
                    self._close_position(open_position, current_price, i)
                    open_position = None
                elif open_position['direction'] == 'SHORT' and current_price >= open_position['stop_loss']:
                    self._close_position(open_position, current_price, i)
                    open_position = None
            
            # --- Signal Generation Logic (Simplified) ---
            # In a real backtest, this would simulate the entire AI/Signal pipeline
            # Here, we use a simple moving average crossover as a stand-in
            if i > 50 and not open_position:
                sma_short = data['close'][i-20:i].mean()
                sma_long = data['close'][i-50:i].mean()
                
                if sma_short > sma_long: # Bullish signal
                    stop_loss = current_price * 0.95
                    size = self.position_sizer.calculate_size(current_price, stop_loss)
                    open_position = self._open_position('LONG', current_price, size, stop_loss, i)
                
                elif sma_short < sma_long: # Bearish signal
                    stop_loss = current_price * 1.05
                    size = self.position_sizer.calculate_size(current_price, stop_loss)
                    open_position = self._open_position('SHORT', current_price, size, stop_loss, i)

            self.equity_curve.append(self.capital)

        logger.info(f"Backtest finished. Final Equity: ${self.capital:,.2f}")
        return self.trades, pd.Series(self.equity_curve, index=data.index)

    def _open_position(self, direction, price, size, stop_loss, timestamp):
        trade = {
            "direction": direction,
            "entry_price": price,
            "size": size,
            "stop_loss": stop_loss,
            "entry_date": timestamp,
        }
        self.trades.append(trade)
        logger.info(f"OPEN {direction} @ {price:.2f} on {timestamp}")
        return trade

    def _close_position(self, position, price, timestamp):
        pnl = (price - position['entry_price']) * position['size']
        if position['direction'] == 'SHORT':
            pnl = -pnl
            
        self.capital += pnl
        position['exit_price'] = price
        position['exit_date'] = timestamp
        position['pnl'] = pnl
        logger.info(f"CLOSE {position['direction']} @ {price:.2f} on {timestamp} | P&L: ${pnl:,.2f}")

```python
# src/backtesting/performance_analyzer.py
# Calculates and displays key performance metrics from a backtest.

import pandas as pd
import numpy as np

class PerformanceAnalyzer:
    """
    Analyzes the results of a backtest (trades and equity curve)
    to calculate key performance indicators (KPIs).
    """
    def __init__(self, trades: list, equity_curve: pd.Series):
        self.trades_df = pd.DataFrame(trades)
        self.equity_curve = equity_curve

    def calculate_metrics(self) -> dict:
        """Calculates all key performance metrics."""
        if self.trades_df.empty:
            return {"error": "No trades were made."}

        total_trades = len(self.trades_df)
        pnl = self.trades_df['pnl']
        
        # Profitability
        gross_profit = pnl[pnl > 0].sum()
        gross_loss = abs(pnl[pnl < 0].sum())
        net_profit = gross_profit - gross_loss
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Trade Stats
        winning_trades = pnl[pnl > 0]
        losing_trades = pnl[pnl < 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = winning_trades.mean()
        avg_loss = abs(losing_trades.mean())
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf

        # Risk & Return
        returns = self.equity_curve.pct_change().dropna()
        sharpe_ratio = self.calculate_sharpe(returns)
        max_drawdown = self.calculate_max_drawdown()

        metrics = {
            "Net Profit": f"${net_profit:,.2f}",
            "Total Trades": total_trades,
            "Win Rate": f"{win_rate:.2%}",
            "Profit Factor": f"{profit_factor:.2f}",
            "Average Win": f"${avg_win:,.2f}",
            "Average Loss": f"${avg_loss:,.2f}",
            "Win/Loss Ratio": f"{win_loss_ratio:.2f}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Max Drawdown": f"{max_drawdown:.2%}",
        }
        return metrics

    def calculate_sharpe(self, returns, risk_free_rate=0.02):
        """Calculates the annualized Sharpe Ratio."""
        # Assuming daily returns, 252 trading days in a year
        excess_returns = returns - (risk_free_rate / 252)
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() != 0 else 0

    def calculate_max_drawdown(self):
        """Calculates the maximum drawdown from the equity curve."""
        roll_max = self.equity_curve.cummax()
        drawdown = (self.equity_curve - roll_max) / roll_max
        return abs(drawdown.min())

    def print_report(self):
        """Prints a formatted report of the performance metrics."""
        metrics = self.calculate_metrics()
        print("\n--- Backtest Performance Report ---")
        for key, value in metrics.items():
            print(f"{key:<20} {value}")
        print("-----------------------------------")

