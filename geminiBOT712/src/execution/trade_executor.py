import redis.asyncio as redis
from database.db_manager import DBManager
from utils.logger import get_logger

logger = get_logger(__name__)

class BaseTradeExecutor:
    def __init__(self, portfolio_capital: float = 10000):
        self.db_manager = DBManager()
        self.redis_client = redis.Redis()
        self.position_sizer = SimpleSizer(portfolio_capital)

    async def process_signal(self, signal: dict):
        raise NotImplementedError

    async def place_trade(self, trade: dict):
        raise NotImplementedError

    async def get_current_price(self, symbol: str) -> float | None:
        return None

class SimpleSizer:
    def __init__(self, capital):
        self.total_capital = capital

    def calculate_size(self, entry_price: float, stop_loss_price: float) -> float:
        return max(self.total_capital * 0.01 / abs(entry_price - stop_loss_price), 0)
