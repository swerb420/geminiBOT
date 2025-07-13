# src/execution/copy_trade_executor.py
# An executor specifically designed to act on copy-trade signals.

from .trade_executor import BaseTradeExecutor
from utils.logger import get_logger
import json

logger = get_logger(__name__)

class CopyTradeExecutor(BaseTradeExecutor):
    """
    Listens for copy-trade signals from the on-chain tracker and executes them.
    Includes signal validation and duplicate prevention.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use a Redis set to keep track of recently processed transaction hashes
        self.processed_txs_key = "copytrade:processed_txs"

    async def listen_for_signals(self):
        """Subscribes to the copy_trade_signals channel."""
        await self.pubsub.subscribe('copy_trade_signals')
        logger.info(f"{self.__class__.__name__} is now listening for on-chain copy-trade signals...")
        
        while True:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message: continue
                
                signal_data = json.loads(message['data'])
                
                # --- 1. Validate Signal ---
                if not self.is_signal_valid(signal_data):
                    logger.warning(f"Received invalid or incomplete copy-trade signal: {signal_data}")
                    continue

                # --- 2. Prevent Duplicate Processing ---
                tx_hash = signal_data['tx_hash']
                if await self.redis_client.sismember(self.processed_txs_key, tx_hash):
                    logger.info(f"Already processed tx {tx_hash}. Skipping.")
                    continue

                logger.info(f"Received new, valid copy-trade signal: {signal_data}")
                await self.process_signal(signal_data)
                
                # Add tx_hash to our set of processed transactions with a TTL of 24 hours
                await self.redis_client.sadd(self.processed_txs_key, tx_hash)
                await self.redis_client.expire(self.processed_txs_key, 86400)

            except json.JSONDecodeError:
                logger.error("Failed to decode message from copy_trade_signals channel.")
            except Exception as e:
                logger.error(f"Error in copy-trade listening loop: {e}", exc_info=True)

    def is_signal_valid(self, signal: dict) -> bool:
        """Checks if the signal contains all the required keys."""
        required_keys = ['tx_hash', 'source_wallet', 'direction', 'leverage']
        return all(key in signal for key in required_keys)

    async def process_signal(self, signal: dict):
        """Processes a validated copy-trade signal."""
        direction = signal['direction']
        leverage = signal['leverage']
        # For our own safety, we use our own position sizer, not the whale's size.
        size = self.position_sizer.total_capital * 0.01 * leverage # Risk 1% of capital with leverage
        
        logger.critical(f"--- EXECUTING COPY TRADE (SIMULATED) ---")
        logger.critical(f"Whale Action: {direction} with {leverage}x leverage.")
        logger.critical(f"Our Action: Opening {direction} position with size {size:.2f}")
        logger.critical(f"--------------------------------------")
        
        # This would be a call to your GMX/Hyperliquid trading function.
        # await self.gmx_trader.open_position(direction, size, leverage)
        
        # Save the signal for tracking
        await self.db_manager.save_signal(signal)

    # These methods are not used by this specific executor
    async def place_trade(self, signal: dict, signal_id: int, entry_price: float, stop_loss: float, size: float):
        pass
    async def get_current_price(self, symbol: str) -> float | None:
        pass
