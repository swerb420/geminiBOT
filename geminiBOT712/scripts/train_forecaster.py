# scripts/train_forecaster.py
# Script to train the TimeSeriesTransformer model with professional-grade features and techniques.

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
import asyncio
from src.database.db_manager import DBManager
from src.ai_analysis.price_forecaster import TimeSeriesTransformer
from src.utils.logger import get_logger
import joblib
import pandas_ta as ta # For advanced feature engineering

logger = get_logger(__name__)

async def prepare_training_data(symbol: str, sequence_length=120, prediction_horizon=12):
    """
    Prepares training data with a rich set of technical indicators.
    """
    db = DBManager()
    await db.connect()
    
    price_history = await db.get_historical_data(symbol, limit=5000)
    if len(price_history) < sequence_length + prediction_horizon + 100: # Need extra for indicator warm-up
        await db.disconnect()
        return None, None
    
    # --- Advanced Feature Engineering using pandas-ta ---
    logger.info("Engineering advanced technical features...")
    price_history.ta.rsi(length=14, append=True)
    price_history.ta.macd(fast=12, slow=26, append=True)
    price_history.ta.bbands(length=20, append=True)
    price_history.ta.atr(length=14, append=True)
    price_history.ta.ema(length=50, append=True)
    
    # Create percentage change features
    price_history['price_pct_change'] = price_history['close'].pct_change()
    
    # --- Label Creation ---
    price_history['future_pct_change'] = price_history['close'].pct_change(periods=prediction_horizon).shift(-prediction_horizon)
    
    # --- Clean and Select Features ---
    price_history = price_history.replace([np.inf, -np.inf], np.nan).dropna()
    
    feature_columns = [
        'price_pct_change', 'RSI_14', 'MACD_12_26_9', 
        'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'ATRr_14'
    ]
    
    # --- Create Sequences ---
    X, y = [], []
    for i in range(len(price_history) - sequence_length):
        X.append(price_history[feature_columns].iloc[i:i+sequence_length].values)
        y.append(price_history['future_pct_change'].iloc[i+sequence_length-1])
        
    await db.disconnect()
    logger.info(f"Created {len(X)} training sequences.")
    return np.array(X), np.array(y)

async def main():
    logger.info("--- Starting Professional Model Training Pipeline ---")
    
    # --- Config ---
    SYMBOL_TO_TRAIN = "BTC-USD"
    SEQUENCE_LENGTH = 120 # 5 days of hourly data
    PREDICTION_HORIZON = 12 # Predict 12 hours ahead
    EPOCHS = 50 # Train for more epochs with early stopping
    
    # 1. Prepare Data
    X, y = await prepare_training_data(SYMBOL_TO_TRAIN, SEQUENCE_LENGTH, PREDICTION_HORIZON)
    if X is None:
        logger.critical(f"Not enough data to train model for {SYMBOL_TO_TRAIN}.")
        return

    # --- Train-Validation Split ---
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_val_tensor = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
    
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    # 2. Initialize Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    num_features = X.shape[2] 
    model = TimeSeriesTransformer(num_features=num_features, d_model=64, nhead=4, d_hid=128, nlayers=3, dropout=0.2).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0005)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5) # Learning rate scheduler

    # 3. Training Loop with Early Stopping
    best_val_loss = float('inf')
    patience_counter = 0
    patience = 5 # Stop after 5 epochs with no improvement

    for epoch in range(EPOCHS):
        model.train()
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            output = model(batch_X)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
        
        # Validation loop
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                output = model(batch_X)
                val_loss += criterion(output, batch_y).item()
        
        avg_val_loss = val_loss / len(val_loader)
        scheduler.step(avg_val_loss)
        logger.info(f"Epoch {epoch+1}/{EPOCHS}, Validation Loss: {avg_val_loss:.6f}")

        # Early Stopping Check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            torch.save(model.state_dict(), "models/price_transformer_best.pth")
            logger.info(f"New best model saved with validation loss: {best_val_loss:.6f}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping triggered.")
                break

    logger.info("--- Training complete. Best model saved as price_transformer_best.pth ---")

if __name__ == "__main__":
    asyncio.run(main())
