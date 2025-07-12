# src/ai_analysis/fed_predictor.py
# Analyzes economic data to predict Federal Reserve policy changes.

from utils.logger import get_logger
import json

logger = get_logger(__name__)

class FedPredictor:
    """
    Analyzes macroeconomic indicators from FRED to predict the probability
    of future Federal Reserve actions (e.g., interest rate hikes/cuts).
    """
    def __init__(self):
        # This would hold the state of key economic indicators
        self.economic_state = {}

    def analyze_economic_data(self, data: dict) -> dict | None:
        """
        Processes a new piece of economic data and updates the prediction.

        Args:
            data (dict): A data point from the FRED ingester.
                         e.g., {'series_id': 'CPIAUCSL', 'value': '3.5'}

        Returns:
            A dictionary with a prediction, or None.
        """
        series_id = data.get('series_id')
        value = float(data.get('value', 0))
        if not series_id:
            return None

        self.economic_state[series_id] = value

        # --- Predictive Logic (Simplified Example) ---
        # This is where a trained econometric model or a complex rule-based
        # system would reside.
        
        cpi = self.economic_state.get('CPIAUCSL', 0) # Inflation
        unrate = self.economic_state.get('UNRATE', 100) # Unemployment
        
        prediction = {"hike_probability": 0.5, "cut_probability": 0.5, "confidence": 0.5}

        # Example Rule: If inflation is high and unemployment is low, probability of a hike increases.
        if cpi > 3.0 and unrate < 4.0:
            prediction['hike_probability'] = 0.80
            prediction['cut_probability'] = 0.10
            prediction['confidence'] = 0.75
            logger.info("Fed Predictor: Conditions suggest a higher probability of a rate HAWKISH stance.")
        
        # Example Rule: If inflation is low and unemployment is high, probability of a cut increases.
        elif cpi < 2.5 and unrate > 4.5:
            prediction['hike_probability'] = 0.10
            prediction['cut_probability'] = 0.80
            prediction['confidence'] = 0.75
            logger.info("Fed Predictor: Conditions suggest a higher probability of a DOVISH stance.")
        
        return prediction

```python
# src/ai_analysis/earnings_predictor.py
# Predicts the likelihood of an earnings beat or miss.

from utils.logger import get_logger
import json

logger = get_logger(__name__)

class EarningsPredictor:
    """
    Analyzes fundamental data, analyst ratings, and other clues to predict
    the likelihood of a company beating or missing earnings estimates.
    """
    def __init__(self):
        pass

    def analyze(self, fundamentals: dict, analyst_ratings: list) -> dict | None:
        """
        Generates an earnings surprise prediction.

        Args:
            fundamentals (dict): Company overview from Alpha Vantage.
            analyst_ratings (list): List of recent ratings from Finviz.

        Returns:
            A prediction dictionary or None.
        """
        if not fundamentals or not analyst_ratings:
            return None

        # --- Predictive Logic (Simplified Example) ---
        beat_score = 0
        miss_score = 0

        # 1. Analyze Analyst Revisions. Upgrades are a positive sign.
        upgrades = sum(1 for r in analyst_ratings if r['action'].lower() in ['upgrade', 'reiterated'])
        downgrades = sum(1 for r in analyst_ratings if r['action'].lower() in ['downgrade'])
        
        beat_score += upgrades * 20
        miss_score += downgrades * 20

        # 2. Analyze Price-to-Earnings (P/E) Ratio. A very high P/E might imply high expectations.
        try:
            pe_ratio = float(fundamentals.get('PERatio', 50))
            if pe_ratio > 100:
                miss_score += 15 # High expectations are harder to beat
        except (ValueError, TypeError):
            pass

        # 3. Analyze recent ratings. More "Buy" ratings are positive.
        buy_ratings = sum(1 for r in analyst_ratings if r['rating'].lower() in ['buy', 'outperform', 'overweight'])
        beat_score += buy_ratings * 10
        
        total_score = beat_score + miss_score
        if total_score == 0: return None

        prediction = {
            "prediction": "BEAT" if beat_score > miss_score else "MISS",
            "confidence": abs(beat_score - miss_score) / total_score
        }

        logger.info(f"Earnings Prediction for {fundamentals['Symbol']}: {prediction['prediction']} "
                    f"with confidence {prediction['confidence']:.2f}")

        return prediction
