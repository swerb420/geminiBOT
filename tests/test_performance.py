import sys, os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geminiBOT712"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geminiBOT712", "src"))

from src.backtesting.performance_analyzer import PerformanceAnalyzer


def test_metrics_include_sortino_and_cagr():
    trades = [{"pnl": 10}, {"pnl": -5}]
    equity = pd.Series([100, 110, 105])
    analyzer = PerformanceAnalyzer(trades, equity)
    metrics = analyzer.calculate_metrics()
    assert "Sortino Ratio" in metrics
    assert "CAGR" in metrics
