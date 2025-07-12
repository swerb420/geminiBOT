# src/ai_analysis/pattern_matcher.py
# Analyzes price data to identify historical chart patterns.

from utils.logger import get_logger
import pandas as pd

logger = get_logger(__name__)

class PatternMatcher:
    """
    Identifies technical analysis patterns from historical price data.
    This is a simplified example. A real system would use more sophisticated
    libraries (like TA-Lib) or machine learning models.
    """
    def __init__(self):
        pass

    def analyze(self, price_history: pd.DataFrame) -> list:
        """
        Analyzes a DataFrame of historical prices to find patterns.

        Args:
            price_history (pd.DataFrame): DataFrame with 'timestamp', 'open', 
                                          'high', 'low', 'close', 'volume' columns.

        Returns:
            A list of found patterns (e.g., {'pattern': 'head_and_shoulders', 'confidence': 0.7}).
        """
        patterns_found = []
        if len(price_history) < 50:
            # Not enough data for meaningful patterns
            return patterns_found

        # --- Example: Simple Moving Average (SMA) Crossover ---
        sma_short = price_history['close'].rolling(window=20).mean()
        sma_long = price_history['close'].rolling(window=50).mean()

        # Check for a recent bullish crossover (short SMA crosses above long SMA)
        if sma_short.iloc[-2] < sma_long.iloc[-2] and sma_short.iloc[-1] > sma_long.iloc[-1]:
            patterns_found.append({
                "pattern": "SMA_20_50_bullish_crossover",
                "confidence": 0.65 # Assign a base confidence score
            })
            logger.info(f"Pattern detected for symbol: SMA Bullish Crossover")

        # Check for a recent bearish crossover
        if sma_short.iloc[-2] > sma_long.iloc[-2] and sma_short.iloc[-1] < sma_long.iloc[-1]:
            patterns_found.append({
                "pattern": "SMA_20_50_bearish_crossover",
                "confidence": 0.65
            })
            logger.info(f"Pattern detected for symbol: SMA Bearish Crossover")
            
        # --- Placeholder for more complex patterns ---
        # e.g., Head and Shoulders, Double Top/Bottom, RSI divergence, etc.

        return patterns_found

```python
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
