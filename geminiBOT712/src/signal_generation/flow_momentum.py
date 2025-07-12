# src/signal_generation/flow_momentum.py
# Algorithm to detect momentum based on unusual options flow.

from utils.logger import get_logger

logger = get_logger(__name__)

class FlowMomentumAlgorithm:
    """
    Analyzes unusual options flow data to generate directional signals.
    """
    def __init__(self, premium_threshold=100000, volume_threshold=3.0):
        """
        Initializes the algorithm with configurable thresholds.

        Args:
            premium_threshold (int): Minimum premium size to consider ($100K).
            volume_threshold (float): Standard deviation for unusual volume.
        """
        self.premium_threshold = premium_threshold
        self.volume_threshold = volume_threshold

    def analyze_flow(self, flow_data: list) -> list:
        """
        Analyzes a list of flow records and generates signals.

        Args:
            flow_data (list): A list of dictionaries, each representing an options trade.

        Returns:
            A list of signal dictionaries.
        """
        signals = []
        if not flow_data:
            return signals

        for trade in flow_data:
            # Basic validation of the trade data structure
            if not all(k in trade for k in ['symbol', 'premium', 'volume', 'open_interest', 'type']):
                continue

            # 1. Filter by significant premium
            if trade['premium'] < self.premium_threshold:
                continue

            # 2. Detect unusual volume (placeholder logic)
            # A real implementation would compare current volume to a historical average.
            # Here, we simulate this with a check against open interest.
            if trade['volume'] < (trade['open_interest'] * self.volume_threshold):
                continue

            # 3. Determine direction from trade type (call/put)
            direction = 'BULLISH' if trade['type'] == 'call' else 'BEARISH'

            # 4. Generate a confidence score (placeholder logic)
            # A real score would factor in urgency, size, sector trends, etc.
            confidence = 70 + (trade['premium'] / 500000) * 10 # Scale score with premium
            confidence = min(confidence, 95.0) # Cap confidence

            signal = {
                "symbol": trade['symbol'],
                "direction": direction,
                "confidence_score": round(confidence, 2),
                "source": "flow_momentum",
                "details": {
                    "premium": trade['premium'],
                    "volume": trade['volume'],
                    "type": trade['type']
                }
            }
            signals.append(signal)
            logger.info(f"Generated signal: {signal['symbol']} {signal['direction']} "
                        f"with confidence {signal['confidence_score']:.2f}")

        return signals
```python
# src/risk_management/position_sizer.py
# Implements different strategies for calculating trade position size.

from utils.logger import get_logger
from config.trading_config import MAX_RISK_PER_TRADE

logger = get_logger(__name__)

class PositionSizer:
    """
    Calculates the appropriate position size for a trade based on risk parameters.
    """
    def __init__(self, strategy='fixed_fractional', total_capital=10000):
        """
        Initializes the position sizer.

        Args:
            strategy (str): The sizing strategy to use ('fixed_fractional', 'kelly_criterion').
            total_capital (float): The total trading capital available.
        """
        if strategy not in ['fixed_fractional', 'kelly_criterion']:
            raise ValueError("Invalid position sizing strategy.")
        self.strategy = strategy
        self.total_capital = total_capital

    def calculate_size(self, entry_price: float, stop_loss_price: float, win_probability=0.75, avg_win_loss_ratio=2.5) -> float:
        """
        Calculates the position size in shares or contracts.

        Args:
            entry_price (float): The expected entry price of the asset.
            stop_loss_price (float): The price at which to exit for a loss.
            win_probability (float): The historical win probability of the strategy.
            avg_win_loss_ratio (float): The historical ratio of average win to average loss.

        Returns:
            The number of shares/contracts to trade, or 0 if risk is invalid.
        """
        if self.strategy == 'fixed_fractional':
            return self._fixed_fractional(entry_price, stop_loss_price)
        elif self.strategy == 'kelly_criterion':
            return self._kelly_criterion(entry_price, stop_loss_price, win_probability, avg_win_loss_ratio)
        return 0.0

    def _fixed_fractional(self, entry_price: float, stop_loss_price: float) -> float:
        """
        Calculates size based on a fixed risk percentage of capital.
        """
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share <= 0:
            logger.warning("Invalid risk per share (<= 0). Cannot calculate position size.")
            return 0.0

        risk_amount = self.total_capital * MAX_RISK_PER_TRADE
        position_size = risk_amount / risk_per_share
        logger.info(f"Fixed Fractional Size: {position_size:.2f} units for risk amount ${risk_amount:.2f}")
        return position_size

    def _kelly_criterion(self, entry_price: float, stop_loss_price: float, win_prob: float, win_loss_ratio: float) -> float:
        """
        Calculates the fraction of capital to risk using the Kelly Criterion.
        """
        if win_loss_ratio <= 0:
            logger.warning("Win/loss ratio must be positive for Kelly Criterion.")
            return 0.0

        # Calculate Kelly fraction
        kelly_fraction = win_prob - ((1 - win_prob) / win_loss_ratio)

        if kelly_fraction <= 0:
            logger.info("Kelly Criterion suggests not to bet (fraction <= 0).")
            return 0.0

        # Use a fractional Kelly to be less aggressive (e.g., half-Kelly)
        kelly_fraction *= 0.5

        # Ensure the fraction doesn't exceed the max risk per trade
        risk_fraction = min(kelly_fraction, MAX_RISK_PER_TRADE)

        risk_amount = self.total_capital * risk_fraction
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share <= 0:
            return 0.0

        position_size = risk_amount / risk_per_share
        logger.info(f"Kelly Criterion Size: {position_size:.2f} units for risk fraction {risk_fraction:.2%}")
        return position_size

# Example Usage
if __name__ == '__main__':
    sizer = PositionSizer(strategy='kelly_criterion', total_capital=10000)
    size = sizer.calculate_size(entry_price=150.0, stop_loss_price=145.0, win_probability=0.75, avg_win_loss_ratio=2.5)
    print(f"Calculated Position Size: {size:.2f} shares")

    sizer_ff = PositionSizer(strategy='fixed_fractional', total_capital=10000)
    size_ff = sizer_ff.calculate_size(entry_price=150.0, stop_loss_price=145.0)
    print(f"Calculated Fixed Fractional Size: {size_ff:.2f} shares")
