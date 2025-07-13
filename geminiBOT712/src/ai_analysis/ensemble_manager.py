# src/ai_analysis/ensemble_manager.py
# The central nervous system of the AI pipeline.

import asyncio
import json
import redis.asyncio as redis
from config.settings import REDIS_HOST, REDIS_PORT
from utils.logger import get_logger
from ai_analysis.sentiment_analyzer import SentimentAnalyzer
from ai_analysis.feature_engine import FeatureEngine # NEW
from ai_analysis.magnitude_predictor import MagnitudePredictor # NEW
# ... other imports

logger = get_logger(__name__)

class EnsembleManager:
    """
    Listens to data streams, runs them through a feature engine,
    and uses predictive models to generate advanced insights.
    """
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        
        # Initialize ALL analysis components
        self.sentiment_analyzer = SentimentAnalyzer()
        self.feature_engine = FeatureEngine()
        self.magnitude_predictor = MagnitudePredictor()
        # ... other analyzers

    async def listen(self):
        """Subscribes to all relevant data channels and processes messages."""
        await self.pubsub.subscribe('news_articles', 'tweets', 'reddit_posts', 'options_flow')
        logger.info("EnsembleManager is now listening for data to feed into the predictive engine...")
        
        while True:
            # ... (message processing loop remains the same) ...
            # Route data to the correct processor
            if channel in ['news_articles', 'tweets', 'reddit_posts']:
                # This is now the main trigger for the predictive pipeline
                await self.run_predictive_pipeline(data)
            # ... other processors

    async def run_predictive_pipeline(self, news_data: dict):
        """
        The core pipeline for generating a magnitude prediction.
        1. Analyze sentiment.
        2. Create features.
        3. Make prediction.
        4. Store insight.
        """
        text = news_data.get('title') or news_data.get('text')
        symbols = news_data.get('symbols', [word.replace('$', '') for word in text.split() if word.startswith('$')])
        if not text or not symbols: return

        for symbol in symbols:
            # Step 1: Analyze and store base sentiment
            sentiment = self.sentiment_analyzer.analyze(text)
            if not sentiment: continue
            await self.store_insight(symbol, 'text_sentiment', sentiment, 3600)

            # Step 2: Create feature vector
            # This needs access to other insights in Redis, so we pass the client
            features = await self.feature_engine.create_features_for_news(symbol, news_data, self.redis_client)
            if not features: continue

            # Step 3: Make prediction
            prediction = self.magnitude_predictor.predict(features)
            if not prediction: continue

            # Step 4: Store the final, advanced insight
            await self.store_insight(symbol, 'magnitude_prediction', prediction, 3600) # 1h TTL

    async def store_insight(self, symbol: str, insight_type: str, data: dict, ttl: int):
        key = f"insight:{symbol}:{insight_type}"
        value = json.dumps(data)
        await self.redis_client.set(key, value, ex=ttl)
        logger.debug(f"Stored {insight_type} for {symbol}")

    # ... other methods ...
    async def run(self):
        await self.listen()
```python
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
