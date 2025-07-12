# src/utils/logger.py
# Standardized logger configuration for the entire application.

import logging
import sys
from config.settings import LOG_LEVEL, LOG_FORMAT

def get_logger(name: str) -> logging.Logger:
    """
    Creates and configures a logger instance.

    Args:
        name (str): The name for the logger, typically __name__.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        # Console Handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(stream_handler)

        # File Handler
        file_handler = logging.FileHandler("trading_system.log")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger
```python
# src/utils/encryption.py
# Handles the encryption and decryption of API keys.

from cryptography.fernet import Fernet
from config.settings import ENCRYPTION_KEY, ENCRYPTED_KEYS_PATH
from utils.logger import get_logger
import json
import os

logger = get_logger(__name__)

class KeyManager:
    """
    Manages loading and decrypting API keys.
    """
    def __init__(self):
        if not ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY is not set in the environment.")
        self.fernet = Fernet(ENCRYPTION_KEY.encode())
        self.keys = self._load_keys()

    def _load_keys(self) -> dict:
        """Loads and decrypts keys from the encrypted file."""
        if not os.path.exists(ENCRYPTED_KEYS_PATH):
            logger.critical(f"Encrypted keys file not found at: {ENCRYPTED_KEYS_PATH}")
            raise FileNotFoundError("Encrypted keys file not found.")

        with open(ENCRYPTED_KEYS_PATH, 'rb') as f:
            encrypted_data = f.read()

        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())

    def get_key(self, service: str):
        """
        Retrieves a decrypted API key for a given service.
        
        Args:
            service (str): The name of the service (e.g., 'unusual_whales').
        
        Returns:
            The API key or None if not found.
        """
        return self.keys.get(service)

def encrypt_keys_from_env():
    """
    Encrypts API keys found in the environment variables and saves them to a file.
    This function is intended to be called from a script.
    """
    logger.info("Starting API key encryption process...")
    if not ENCRYPTION_KEY:
        logger.critical("ENCRYPTION_KEY environment variable not set. Cannot encrypt.")
        return

    fernet = Fernet(ENCRYPTION_KEY.encode())
    
    keys_to_encrypt = {
        "unusual_whales": os.getenv("UNUSUAL_WHALES_API_KEY"),
        "bigshort": os.getenv("BIGSHORT_API_KEY"),
        "stalkchain": os.getenv("STALKCHAIN_API_KEY"),
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret_key": os.getenv("TWITTER_API_SECRET_KEY"),
        "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "twitter_access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    }

    # Filter out keys that are not set
    keys_to_encrypt = {k: v for k, v in keys_to_encrypt.items() if v}
    
    if not keys_to_encrypt:
        logger.warning("No API keys found in environment variables to encrypt.")
        return

    logger.info(f"Encrypting keys for services: {list(keys_to_encrypt.keys())}")
    
    json_data = json.dumps(keys_to_encrypt).encode()
    encrypted_data = fernet.encrypt(json_data)

    with open(ENCRYPTED_KEYS_PATH, 'wb') as f:
        f.write(encrypted_data)
    
    logger.info(f"Successfully encrypted keys and saved to {ENCRYPTED_KEYS_PATH}")

if __name__ == '__main__':
    # This script can be run to perform the encryption
    # `python -m src.utils.encryption`
    from dotenv import load_dotenv
    load_dotenv()
    encrypt_keys_from_env()
