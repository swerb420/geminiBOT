# src/ai_analysis/magnitude_predictor.py
# Uses a trained ML model to predict the magnitude of a price move.

from utils.logger import get_logger
import joblib # For loading pre-trained models
import pandas as pd

logger = get_logger(__name__)

class MagnitudePredictor:
    """
    Uses a pre-trained machine learning model (e.g., LightGBM, XGBoost)
    to predict the potential percentage price change based on a feature vector.
    """
    def __init__(self, model_path="models/magnitude_model.pkl"):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Loads the pre-trained model from disk."""
        try:
            # In a real system, you would train this model on historical data
            # and save it using joblib. For now, we'll simulate it if it doesn't exist.
            self.model = joblib.load(self.model_path)
            logger.info(f"Magnitude prediction model loaded from {self.model_path}")
        except FileNotFoundError:
            logger.warning(f"Prediction model not found at {self.model_path}. The predictor will use a dummy logic.")
            self.model = None # Set to None to indicate we need to use dummy logic
        except Exception as e:
            logger.error(f"Error loading prediction model: {e}", exc_info=True)
            self.model = None

    def predict(self, features: dict) -> dict | None:
        """
        Predicts the magnitude and direction of a price move.

        Args:
            features (dict): A dictionary of numerical features from the FeatureEngine.

        Returns:
            A dictionary containing the predicted move and confidence.
        """
        if not features:
            return None

        if self.model:
            # Use the actual trained model
            feature_df = pd.DataFrame([features])
            prediction = self.model.predict(feature_df)[0]
            # Assuming the model outputs a single float (e.g., 2.5 for +2.5%)
            predicted_pct_change = float(prediction)
            confidence = 0.85 # This could also be an output of the model
        else:
            # --- Dummy Logic if no model is loaded ---
            # A simple weighted sum as a placeholder for a real ML model.
            base_prediction = features['sentiment_score'] * features['sentiment_label'] * 5 # Predict up to 5% move
            
            # Boost prediction if flow confirms it
            if features['flow_confirms_sentiment'] == 1:
                base_prediction *= 1.5
            
            # Weight by source trust
            predicted_pct_change = base_prediction * features['source_trust']
            confidence = (features['source_trust'] + features['sentiment_score']) / 2

        if abs(predicted_pct_change) < 0.5: # Ignore trivial predicted moves
            return None

        result = {
            "predicted_pct_change": round(predicted_pct_change, 2),
            "confidence": round(confidence, 2),
            "direction": "BULLISH" if predicted_pct_change > 0 else "BEARISH"
        }
        logger.info(f"Magnitude Prediction: {result}")
        return result

