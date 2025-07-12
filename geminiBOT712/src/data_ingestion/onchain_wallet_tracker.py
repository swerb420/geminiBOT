# src/data_ingestion/onchain_wallet_tracker.py
# Listens to on-chain events to track whale wallets and copy-trade signals.

from .base_ingester import BaseIngester
from utils.logger import get_logger
from web3 import Web3
from web3.exceptions import ABIDecodingError, BlockNotFound
import json
import asyncio

logger = get_logger(__name__)

class OnChainWalletTracker(BaseIngester):
    """
    Connects to a blockchain node (via RPC) to monitor specific wallets
    and smart contracts (e.g., GMX, Hyperliquid) for large trades.
    This version includes robust error handling and reconnection logic.
    """
    def __init__(self, rpc_url: str, wallets_to_track: list, contracts_to_monitor: dict):
        super().__init__()
        self.rpc_url = rpc_url
        self.wallets_to_track = [Web3.to_checksum_address(w) for w in wallets_to_track]
        self.contracts = {Web3.to_checksum_address(k): v for k, v in contracts_to_monitor.items()}
        self.w3 = None
        self.is_running = True

    async def connect(self):
        """Establishes a connection to the WebSocket RPC provider."""
        logger.info(f"Attempting to connect to blockchain RPC at {self.rpc_url}...")
        self.w3 = Web3(Web3.WebsocketProvider(self.rpc_url))
        if await self.w3.is_connected():
            logger.info("Successfully connected to blockchain RPC.")
            return True
        else:
            logger.critical("Failed to connect to blockchain RPC.")
            self.w3 = None
            return False

    async def run(self, interval_seconds: int = 0):
        """
        The main loop that maintains a connection and listens for blocks.
        Includes exponential backoff for reconnection attempts.
        """
        reconnect_delay = 5  # Start with a 5-second delay
        while self.is_running:
            if not self.w3 or not await self.w3.is_connected():
                if not await self.connect():
                    logger.info(f"Retrying connection in {reconnect_delay} seconds...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 300) # Exponential backoff up to 5 minutes
                    continue
            
            reconnect_delay = 5 # Reset delay on successful connection
            logger.info(f"Starting on-chain tracker for {len(self.wallets_to_track)} wallets...")
            
            try:
                block_filter = await self.w3.eth.filter('latest')
                async for block_hash in block_filter.watch_changes():
                    try:
                        block = await self.w3.eth.get_block(block_hash, full_transactions=True)
                        if not block: continue
                        logger.debug(f"Processing block #{block.number}")
                        for tx in block.transactions:
                            await self.process_transaction(tx)
                    except BlockNotFound:
                        logger.warning(f"Block {block_hash.hex()} not found. Likely a chain reorg. Skipping.")
                    except Exception as e:
                        logger.error(f"Error processing block {block_hash.hex()}: {e}")
            except Exception as e:
                logger.error(f"Connection to RPC lost or filter error: {e}. Attempting to reconnect...")
                self.w3 = None # Force a reconnect in the next loop iteration
                await asyncio.sleep(5)

    async def process_transaction(self, tx):
        """Analyzes a single transaction to see if it's relevant."""
        tx_from = tx.get('from')
        tx_to = tx.get('to')
        
        if not tx_from or not tx_to: return

        if tx_from not in self.wallets_to_track or tx_to not in self.contracts:
            return

        logger.info(f"Detected relevant transaction {tx.hash.hex()} from tracked wallet {tx_from} to contract {tx_to}")
        
        contract = self.w3.eth.contract(address=tx_to, abi=self.contracts[tx_to]['abi'])
        try:
            func_obj, func_params = contract.decode_function_input(tx.input)
            
            # Example: If we detect a "submit_order" function call
            if func_obj.fn_name == 'submitOrder':
                size = func_params.get('size')
                is_long = func_params.get('isLong')
                leverage = func_params.get('leverage', 10)
                
                copy_trade_signal = {
                    "tx_hash": tx.hash.hex(), # Include tx hash to prevent duplicates
                    "source_wallet": tx_from,
                    "contract": tx_to,
                    "direction": "LONG" if is_long else "SHORT",
                    "size_usd": size / 1e18 if size else 0,
                    "leverage": leverage
                }
                
                logger.critical(f"COPY TRADE SIGNAL: Wallet {tx_from} opened a {copy_trade_signal['direction']} position!")
                await self.publish_to_redis('copy_trade_signals', copy_trade_signal)

        except ABIDecodingError:
            logger.warning(f"Could not decode transaction input for tx {tx.hash.hex()}. It may be a different function call.")
        except Exception as e:
            logger.error(f"An unexpected error occurred decoding tx {tx.hash.hex()}: {e}")

    async def close(self):
        """Gracefully shuts down the connection."""
        self.is_running = False
        if self.w3 and hasattr(self.w3.provider, 'disconnect'):
            await self.w3.provider.disconnect()
        logger.info("OnChainWalletTracker has been shut down.")

```python
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
