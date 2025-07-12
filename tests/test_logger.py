import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geminiBOT712")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geminiBOT712", "src"))
from src.utils.logger import get_logger

def test_get_logger():
    logger = get_logger("test")
    assert logger.name == "test"
