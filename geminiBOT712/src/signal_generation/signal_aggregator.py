# src/signal_generation/signal_aggregator.py (REVISED)
# The final decision-maker for generating trade signals.

import asyncio
import json
import redis.asyncio as redis
from config.settings import REDIS_HOST, REDIS_PORT
from config.trading_config import MIN_CONFIDENCE_SCORE
from utils.logger import get_logger

logger = get_logger(__name__)

class SignalAggregator:
    """
    This module's role is now simplified. It primarily looks for the
    high-level 'magnitude_prediction' insight and uses it to generate a signal.
    """
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    async def run(self, interval_seconds: int = 5):
        logger.info(f"SignalAggregator started. Looking for magnitude predictions every {interval_seconds}s.")
        while True:
            try:
                # Scan for new magnitude predictions
                async for key in self.redis_client.scan_iter("insight:*:magnitude_prediction"):
                    await self.evaluate_prediction(key)
            except Exception as e:
                logger.error(f"Error in SignalAggregator loop: {e}", exc_info=True)
            await asyncio.sleep(interval_seconds)

    async def evaluate_prediction(self, prediction_key: str):
        """
        Evaluates a magnitude prediction and decides whether to issue a signal.
        """
        prediction_json = await self.redis_client.get(prediction_key)
        if not prediction_json: return
        
        prediction = json.loads(prediction_json)
        symbol = prediction_key.split(':')[1]

        # Use the confidence score from the prediction itself
        confidence = prediction.get('confidence', 0) * 100

        if confidence < MIN_CONFIDENCE_SCORE:
            logger.info(f"Magnitude prediction found for {symbol} but confidence ({confidence:.2f}) is below threshold.")
            # Delete the key so we don't re-evaluate it
            await self.redis_client.delete(prediction_key)
            return

        # --- Generate Final Signal ---
        final_signal = {
            "symbol": symbol,
            "direction": prediction['direction'],
            "confidence_score": round(confidence, 2),
            "predicted_pct_change": prediction['predicted_pct_change'],
            "source_indicators": ["MagnitudePredictorV1"]
        }
        
        # Publish to the trade signals channel for the execution engine
        await self.redis_client.publish('trade_signals', json.dumps(final_signal))
        logger.critical(f"*** PREDICTIVE SIGNAL GENERATED: {final_signal} ***")

        # Delete the key to signify it has been processed
        await self.redis_client.delete(prediction_key)

