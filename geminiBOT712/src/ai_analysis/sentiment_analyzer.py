from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from utils.logger import get_logger
import torch

logger = get_logger(__name__)

class SentimentAnalyzer:
    """Simple wrapper around a Hugging Face sentiment analysis pipeline."""
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        try:
            device = 0 if torch.cuda.is_available() else -1
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=device)
            logger.info("Sentiment analysis model loaded")
        except Exception as e:
            logger.critical(f"Failed to load sentiment model: {e}", exc_info=True)
            self.pipeline = None

    def analyze(self, text: str) -> dict:
        if not self.pipeline or not isinstance(text, str):
            return {}
        try:
            result = self.pipeline([text])[0]
            result['label'] = result['label'].upper()
            return result
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}", exc_info=True)
            return {}
