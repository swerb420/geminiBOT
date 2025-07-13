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
        sortino_ratio = self.calculate_sortino(returns)
        max_drawdown = self.calculate_max_drawdown()
        cagr = self.calculate_cagr()

        metrics = {
            "Net Profit": f"${net_profit:,.2f}",
            "Total Trades": total_trades,
            "Win Rate": f"{win_rate:.2%}",
            "Profit Factor": f"{profit_factor:.2f}",
            "Average Win": f"${avg_win:,.2f}",
            "Average Loss": f"${avg_loss:,.2f}",
            "Win/Loss Ratio": f"{win_loss_ratio:.2f}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Sortino Ratio": f"{sortino_ratio:.2f}",
            "CAGR": f"{cagr:.2%}",
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

    def calculate_sortino(self, returns, risk_free_rate=0.02):
        """Calculates the annualized Sortino Ratio."""
        downside = returns[returns < 0]
        if downside.std() == 0:
            return 0
        excess_returns = returns - (risk_free_rate / 252)
        return np.sqrt(252) * excess_returns.mean() / downside.std()

    def calculate_cagr(self):
        """Computes the compound annual growth rate of the equity curve."""
        if self.equity_curve.empty:
            return 0.0
        start_val = self.equity_curve.iloc[0]
        end_val = self.equity_curve.iloc[-1]
        years = len(self.equity_curve) / 252
        if start_val <= 0 or years <= 0:
            return 0.0
        return (end_val / start_val) ** (1 / years) - 1

    def print_report(self):
        """Prints a formatted report of the performance metrics."""
        metrics = self.calculate_metrics()
        print("\n--- Backtest Performance Report ---")
        for key, value in metrics.items():
            print(f"{key:<20} {value}")
        print("-----------------------------------")

