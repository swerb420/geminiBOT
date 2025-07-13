# src/risk_management/volatility_manager.py
# Calculates volatility metrics to set dynamic risk parameters.

import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

class VolatilityManager:
    """
    Calculates volatility metrics like Average True Range (ATR) to help
    set dynamic, volatility-adjusted stop losses and take profits.
    """
    def __init__(self):
        pass

    def calculate_atr(self, price_history: pd.DataFrame, period: int = 14) -> float:
        """
        Calculates the Average True Range (ATR).

        Args:
            price_history (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns.
            period (int): The lookback period for the ATR calculation.

        Returns:
            The latest ATR value, or 0 if data is insufficient.
        """
        if len(price_history) < period or not all(c in price_history.columns for c in ['high', 'low', 'close']):
            logger.warning("Not enough data or missing HLC columns for ATR calculation.")
            return 0.0

        high_low = price_history['high'] - price_history['low']
        high_close = (price_history['high'] - price_history['close'].shift()).abs()
        low_close = (price_history['low'] - price_history['close'].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        
        latest_atr = atr.iloc[-1]
        logger.debug(f"Calculated latest ATR: {latest_atr:.4f}")
        return latest_atr

    def get_volatility_adjusted_stop_loss(self, entry_price: float, direction: str, atr: float, multiplier: float = 2.0) -> float:
        """
        Calculates a stop loss based on the current ATR.

        Args:
            entry_price (float): The price at which the trade was entered.
            direction (str): 'BULLISH' or 'BEARISH'.
            atr (float): The current Average True Range value.
            multiplier (float): The number of ATRs to place the stop loss away.

        Returns:
            The calculated stop loss price.
        """
        if atr <= 0: # Fallback to a fixed percentage if ATR is invalid
            return entry_price * 0.95 if direction == 'BULLISH' else entry_price * 1.05

        if direction == 'BULLISH':
            stop_loss = entry_price - (atr * multiplier)
        else: # BEARISH
            stop_loss = entry_price + (atr * multiplier)

        return stop_loss

    def trailing_stop(self, current_price: float, existing_stop: float, direction: str,
                       atr: float, multiplier: float = 2.0) -> float:
        """Calculates a new stop loss that trails the current price."""
        if atr <= 0:
            return existing_stop

        if direction == 'BULLISH':
            new_stop = max(existing_stop, current_price - (atr * multiplier))
        else:  # BEARISH
            new_stop = min(existing_stop, current_price + (atr * multiplier))

        return new_stop
