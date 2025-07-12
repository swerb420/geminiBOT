# config/trading_config.py
# Defines risk management parameters and trading strategy settings.

# --- Risk Management ---
MAX_RISK_PER_TRADE = 0.02  # 2% of total capital
MAX_DAILY_LOSS_LIMIT = 0.08  # 8% of total capital
MAX_PORTFOLIO_EXPOSURE = 0.50  # Max 50% of capital deployed at any time

# --- Position Sizing ---
# Options: 'fixed_fractional', 'kelly_criterion'
POSITION_SIZING_STRATEGY = 'kelly_criterion'

# --- Signal Generation ---
MIN_CONFIDENCE_SCORE = 85.0  # Minimum confidence required to execute a trade
REQUIRED_CONFIRMING_INDICATORS = 3

# --- Execution ---
# Set to 'paper' for testing, 'live' for real trading
TRADING_MODE = 'paper'
