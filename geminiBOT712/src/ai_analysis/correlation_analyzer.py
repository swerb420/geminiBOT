# src/ai_analysis/correlation_analyzer.py
# Analyzes the correlation between different assets.

from utils.logger import get_logger
import pandas as pd

logger = get_logger(__name__)

class CorrelationAnalyzer:
    """
    Calculates and analyzes the correlation between a lead asset (e.g., BTC)
    and a lag asset (e.g., a crypto-related stock like MARA or COIN).
    """
    def __init__(self):
        # In a real system, this would be pre-calculated and updated periodically
        self.correlation_matrix = {}

    def analyze(self, lead_asset_history: pd.DataFrame, lag_asset_history: pd.DataFrame) -> dict:
        """
        Analyzes the correlation and recent divergence between two assets.

        Args:
            lead_asset_history (pd.DataFrame): Price history of the leading asset.
            lag_asset_history (pd.DataFrame): Price history of the lagging asset.

        Returns:
            A dictionary with correlation insights.
        """
        if lead_asset_history.empty or lag_asset_history.empty:
            return {}

        # Align dataframes by timestamp
        merged_df = pd.merge(lead_asset_history[['close']], lag_asset_history[['close']], 
                             left_index=True, right_index=True, suffixes=('_lead', '_lag'))
        
        if len(merged_df) < 30:
            return {} # Not enough data to correlate

        # Calculate percentage change
        merged_df['lead_pct_change'] = merged_df['close_lead'].pct_change()
        merged_df['lag_pct_change'] = merged_df['close_lag'].pct_change()

        # Calculate rolling correlation
        rolling_corr = merged_df['lead_pct_change'].rolling(window=30).corr(merged_df['lag_pct_change']).iloc[-1]

        # Check for divergence: e.g., lead asset is up significantly, but lag is not
        lead_change_recent = (merged_df['close_lead'].iloc[-1] / merged_df['close_lead'].iloc[-5]) - 1 # 5-period change
        lag_change_recent = (merged_df['close_lag'].iloc[-1] / merged_df['close_lag'].iloc[-5]) - 1

        divergence = lead_change_recent - lag_change_recent

        insight = {
            "rolling_correlation": round(rolling_corr, 3),
            "divergence_pct": round(divergence * 100, 2)
        }
        
        # If correlation is high and there's a significant positive divergence,
        # it might be a bullish signal for the lagging asset.
        if rolling_corr > 0.7 and divergence > 0.05: # 5% divergence
            insight['signal'] = 'BULLISH_CONVERGENCE'
            logger.info(f"Correlation signal: Bullish convergence detected between assets.")
        
        return insight
