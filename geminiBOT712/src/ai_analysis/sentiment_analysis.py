# src/ai_analysis/sentiment_analyzer.py
# Performs sentiment analysis on text data using a pre-trained model.

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from utils.logger import get_logger
import torch

logger = get_logger(__name__)

class SentimentAnalyzer:
    """
    A wrapper for a Hugging Face sentiment analysis pipeline.
    Uses a model fine-tuned for financial news and auto-detects GPU.
    """
    def __init__(self, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        """
        Loads the sentiment analysis model and tokenizer.
        Handles errors gracefully and attempts to use GPU if available.
        """
        try:
            # Check for GPU
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            logger.info(f"Loading sentiment analysis model: {self.model_name} on {device_name}...")
            
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=device
            )
            logger.info("Sentiment analysis model loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load sentiment analysis model: {e}", exc_info=True)
            logger.warning("Sentiment analysis will be disabled.")

    def analyze(self, text: str) -> dict:
        """
        Analyzes the sentiment of a given piece of text.

        Returns:
            A dictionary with 'label' and 'score', or an empty dict on failure.
        """
        if not self.pipeline:
            return {}

        if not text or not isinstance(text, str):
            return {}

        try:
            # The pipeline expects a list of texts
            results = self.pipeline([text])
            # Normalize label to be consistently uppercase
            result = results[0] if results else {}
            if 'label' in result:
                result['label'] = result['label'].upper() # e.g., POSITIVE, NEGATIVE
            return result
        except Exception as e:
            logger.error(f"Error during sentiment analysis for text: '{text[:50]}...': {e}", exc_info=True)
            return {}

# Example usage:
if __name__ == '__main__':
    analyzer = SentimentAnalyzer()
    if analyzer.pipeline:
        news_headline = "AAPL stock surges after record-breaking iPhone sales report."
        sentiment = analyzer.analyze(news_headline)
        print(f"Headline: '{news_headline}'")
        print(f"Sentiment: {sentiment}")

        news_headline_2 = "Market plunges as new inflation data spooks investors."
        sentiment_2 = analyzer.analyze(news_headline_2)
        print(f"Headline: '{news_headline_2}'")
        print(f"Sentiment: {sentiment_2}")

