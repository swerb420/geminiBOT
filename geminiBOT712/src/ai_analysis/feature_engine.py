# src/ai_analysis/feature_engine.py
# Creates advanced features from raw data for machine learning models.

from utils.logger import get_logger
import pandas as pd
import json
from database.db_manager import DBManager # Import DBManager to get historical data

logger = get_logger(__name__)

class FeatureEngine:
    """
    Takes raw insights and engineers features for predictive models,
    including single-event features and time-series sequences.
    """
    def __init__(self):
        self.db_manager = DBManager() # For fetching historical data
        self.source_trust_scores = {
            "Reuters": 0.9, "Bloomberg": 0.9, "CNBC": 0.8,
            "MarketWatch Scraper": 0.7, "Stocktwits": 0.6,
            "Twitter": 0.5, "Reddit": 0.4
        }

    async def create_features_for_news(self, symbol: str, news_data: dict, redis_client) -> dict | None:
        """
        Creates a feature vector for a single news event (for simpler models).
        """
        features = {}
        sentiment_key = f"insight:{symbol}:text_sentiment"
        sentiment_json = await redis_client.get(sentiment_key)
        if not sentiment_json: return None
        
        sentiment = json.loads(sentiment_json)
        features['sentiment_score'] = sentiment.get('score', 0.5)
        features['sentiment_label'] = 1 if sentiment.get('label') == 'POSITIVE' else -1
        
        source = news_data.get('source', 'Twitter')
        features['source_trust'] = self.source_trust_scores.get(source, 0.5)
        
        flow_key = f"insight:{symbol}:flow_momentum"
        flow_json = await redis_client.get(flow_key)
        if flow_json:
            flow = json.loads(flow_json)
            flow_direction = 1 if flow.get('direction') == 'BULLISH' else -1
            features['flow_confirms_sentiment'] = 1 if flow_direction == features['sentiment_label'] else 0
            features['flow_premium'] = flow.get('details', {}).get('premium', 0)
        else:
            features['flow_confirms_sentiment'] = 0
            features['flow_premium'] = 0

        logger.debug(f"Created feature vector for {symbol}: {features}")
        return features

    async def create_sequence_features(self, symbol: str, sequence_length: int = 120) -> pd.DataFrame | None:
        """
        Creates a time-series feature sequence for the Transformer model.

        Args:
            symbol (str): The stock symbol.
            sequence_length (int): The number of time steps to include (e.g., 120 minutes).

        Returns:
            A pandas DataFrame ready for the forecasting model, or None.
        """
        # 1. Get historical price data from our database
        # We need more than sequence_length to calculate indicators like moving averages
        price_history = await self.db_manager.get_historical_data(symbol, limit=sequence_length + 50)
        if len(price_history) < sequence_length:
            return None

        # 2. Engineer basic technical indicators
        features_df = pd.DataFrame(index=price_history.index)
        features_df['price_pct_change'] = price_history['close'].pct_change()
        features_df['volume_pct_change'] = price_history['volume'].pct_change()
        features_df['sma_5_vs_20'] = (price_history['close'].rolling(5).mean() / price_history['close'].rolling(20).mean()) - 1
        
        # 3. Integrate other data (sentiment, flow)
        # In a production system, you would fetch historical insights from Redis/DB
        # and align them with the price data timestamps. For now, we'll forward-fill.
        features_df['sentiment_score'] = 0.5 # Placeholder
        features_df['flow_premium'] = 0 # Placeholder

        # 4. Clean and prepare the final DataFrame
        features_df = features_df.replace([pd.NA, float('inf'), float('-inf')], 0).fillna(0)
        
        # Return the last `sequence_length` rows
        final_sequence = features_df.tail(sequence_length)
        
        # Ensure the number of features matches the model's expectation
        # This is a critical step.
        # final_sequence = final_sequence[['feat1', 'feat2', ...]] # Select final columns
        
        logger.debug(f"Created sequence of {len(final_sequence)} steps for {symbol}")
        return final_sequence

    async def connect_db(self):
        """Connects the internal DBManager."""
        await self.db_manager.connect()

    async def close_db(self):
        """Closes the internal DBManager connection."""
        await self.db_manager.disconnect()
