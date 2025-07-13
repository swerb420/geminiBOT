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
