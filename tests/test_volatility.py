import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geminiBOT712"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geminiBOT712", "src"))

from src.risk_management.volatility_manager import VolatilityManager


def test_trailing_stop_moves():
    vm = VolatilityManager()
    stop = vm.trailing_stop(current_price=105, existing_stop=100, direction="BULLISH", atr=2, multiplier=1)
    assert stop == 103
    # Should not lower the stop if price falls
    stop2 = vm.trailing_stop(current_price=101, existing_stop=stop, direction="BULLISH", atr=2, multiplier=1)
    assert stop2 == 103
