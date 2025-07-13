# scripts/train_signal_filter.py
# This script trains the self-learning SignalFilter model.

import asyncio
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
from src.database.db_manager import DBManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def fetch_training_data() -> pd.DataFrame:
    """
    Fetches all completed signals from the database to be used as training data.
    """
    db = DBManager()
    await db.connect()
    
    # We need to query the signals table directly with raw SQL for this custom task.
    query = "SELECT * FROM signals WHERE outcome IS NOT NULL;"
    async with db.pool.acquire() as conn:
        records = await conn.fetch(query)
    
    await db.disconnect()
    
    if not records:
        return pd.DataFrame()
        
    return pd.DataFrame(records)

def create_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Performs feature engineering on the raw signal data to prepare it for the model.
    """
    # --- Feature Engineering ---
    # The goal is to turn all data into numerical features.
    
    # 1. One-hot encode the 'direction'
    df['direction_bullish'] = df['direction'].apply(lambda x: 1 if x == 'BULLISH' else 0)
    
    # 2. Extract features from the source_indicators JSON
    # For simplicity, we'll just count the number of indicators for now.
    # A more advanced version would one-hot encode each indicator source.
    df['indicator_count'] = df['source_indicators'].apply(lambda x: len(x) if x else 0)
    
    # --- Define Features (X) and Target (y) ---
    feature_columns = [
        'confidence_score',
        'direction_bullish',
        'indicator_count'
        # In a more advanced system, you would add features for market regime at signal creation time.
    ]
    
    X = df[feature_columns]
    y = df['outcome'] # The target we want to predict ('WIN' or 'LOSS')
    
    return X, y

async def main():
    logger.info("--- Starting Signal Filter Model Training Pipeline ---")
    
    # 1. Fetch Data
    training_df = await fetch_training_data()
    if training_df.empty:
        logger.warning("No completed signals with outcomes found in the database. Cannot train filter model.")
        return
    
    logger.info(f"Fetched {len(training_df)} completed signals to train on.")
    
    # 2. Create Features and Labels
    X, y = create_features(training_df)
    
    # 3. Split Data for Training and Testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 4. Train the Model
    logger.info("Training the Logistic Regression classifier...")
    # Logistic Regression is a good, simple baseline model for classification.
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    # 5. Evaluate the Model
    logger.info("Evaluating model performance on test data...")
    predictions = model.predict(X_test)
    report = classification_report(y_test, predictions)
    logger.info(f"\n--- Model Performance Report ---\n{report}")
    
    # 6. Save the Trained Model
    model_path = "models/signal_filter_model.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Training complete. New Signal Filter model saved to {model_path}")

if __name__ == "__main__":
    # You would run this script periodically (e.g., once a week) to retrain
    # the model as more signal data becomes available.
    asyncio.run(main())
