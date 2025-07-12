# src/ai_analysis/price_forecaster.py
# Uses a Transformer model to forecast future price movements.

import torch
import torch.nn as nn
import math
from utils.logger import get_logger

logger = get_logger(__name__)

# Define the Transformer model architecture
class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:x.size(0)]
        return self.dropout(x)

class TimeSeriesTransformer(nn.Module):
    """
    A Transformer model for time-series forecasting.
    """
    def __init__(self, num_features: int, d_model: int, nhead: int, d_hid: int, nlayers: int, dropout: float = 0.5):
        super().__init__()
        self.model_type = 'Transformer'
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, d_hid, dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, nlayers)
        self.encoder = nn.Linear(num_features, d_model)
        self.d_model = d_model
        self.decoder = nn.Linear(d_model, 1) # Output a single value (predicted price change)

    def forward(self, src: torch.Tensor) -> torch.Tensor:
        src = self.encoder(src) * math.sqrt(self.d_model)
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src)
        # We only care about the prediction from the last time step
        output = self.decoder(output[:, -1, :])
        return output

class PriceForecaster:
    """
    A wrapper for the TimeSeriesTransformer model that handles loading,
    preprocessing, and making predictions.
    """
    def __init__(self, model_path="models/price_transformer.pth", num_features=10):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"PriceForecaster will run on device: {self.device.type}")
        
        # Hyperparameters should match the trained model
        self.model = TimeSeriesTransformer(
            num_features=num_features,
            d_model=64,
            nhead=4,
            d_hid=128,
            nlayers=3,
            dropout=0.2
        ).to(self.device)
        
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval() # Set model to evaluation mode
            logger.info(f"Price forecasting Transformer model loaded from {model_path}")
        except FileNotFoundError:
            logger.warning(f"Forecasting model not found at {model_path}. Predictor will be disabled.")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading forecasting model: {e}", exc_info=True)
            self.model = None

    def forecast(self, sequence_data: pd.DataFrame) -> dict | None:
        """
        Takes a sequence of features and forecasts the next price move.

        Args:
            sequence_data (pd.DataFrame): A DataFrame where rows are time steps
                                          and columns are features.

        Returns:
            A prediction dictionary.
        """
        if self.model is None or sequence_data.empty:
            return None

        # Convert DataFrame to PyTorch tensor
        tensor_input = torch.tensor(sequence_data.values, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            prediction = self.model(tensor_input)
        
        predicted_pct_change = prediction.item()

        result = {
            "predicted_pct_change": round(predicted_pct_change, 4),
            "confidence": 0.80, # Confidence could be derived from model's attention weights
            "forecast_horizon_minutes": 60 # e.g., this model predicts 1 hour ahead
        }
        logger.info(f"Transformer Forecast: {result}")
        return result
