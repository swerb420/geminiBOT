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
