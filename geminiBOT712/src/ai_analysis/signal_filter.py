# src/ai_analysis/signal_filter.py
# A meta-model that learns from past signal performance.

from utils.logger import get_logger
import pandas as pd
from database.db_manager import DBManager
import joblib

logger = get_logger(__name__)

class SignalFilter:
    """
    Uses a trained model to predict the probability of success for a new signal,
    based on the historical performance of similar signals under similar market conditions.
    This is the system's self-learning feedback loop.
    """
    def __init__(self, model_path="models/signal_filter_model.pkl"):
        self.db_manager = DBManager()
        self.model = None
        try:
            self.model = joblib.load(model_path)
            logger.info("Signal Filter model loaded.")
        except FileNotFoundError:
            logger.warning("Signal Filter model not found. All signals will be approved by default.")
        except Exception as e:
            logger.error(f"Error loading Signal Filter model: {e}")

    async def should_approve_signal(self, signal_data: dict, market_regime: str) -> bool:
        """
        Predicts if a signal should be approved for execution.

        Args:
            signal_data (dict): The newly generated signal.
            market_regime (str): The current market regime.

        Returns:
            True if the signal is approved, False otherwise.
        """
        if not self.model:
            return True # Approve all signals if no model is loaded

        # --- Create Feature Vector for the Signal ---
        features = {
            "confidence_score": signal_data['confidence_score'],
            "direction_bullish": 1 if signal_data['direction'] == 'BULLISH' else 0,
            # One-hot encode the market regime
            "regime_bullish": 1 if market_regime == 'BULLISH' else 0,
            "regime_bearish": 1 if market_regime == 'BEARISH' else 0,
            "regime_sideways": 1 if market_regime == 'SIDEWAYS' else 0,
            # Add features for the source indicators...
        }
        
        feature_df = pd.DataFrame([features])
        
        # Predict the probability of this signal being a 'WIN'
        win_probability = self.model.predict_proba(feature_df)[0][1] # Prob of class 1 ('WIN')
        
        logger.info(f"Signal for {signal_data['symbol']} has a predicted win probability of {win_probability:.2%}")
        
        # Approve if the predicted probability is above a threshold (e.g., 65%)
        if win_probability >= 0.65:
            return True
        else:
            logger.warning(f"SIGNAL VETOED: Predicted win probability {win_probability:.2%} is below threshold.")
            return False

    # In a separate script, you would add a `train_filter_model` function
    # that queries the `signals` table, creates a feature set, and trains a
    # classifier (like LogisticRegression or XGBoost) to predict the 'outcome' column.

