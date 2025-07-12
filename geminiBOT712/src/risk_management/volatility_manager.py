class VolatilityManager:
    def calculate_atr(self, prices):
        return 0

    def get_volatility_adjusted_stop_loss(self, entry_price: float, direction: str, atr: float, multiplier: float = 2.0):
        if direction == 'BULLISH':
            return entry_price - atr * multiplier
        else:
            return entry_price + atr * multiplier
