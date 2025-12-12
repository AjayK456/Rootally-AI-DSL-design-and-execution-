# tests/conftest.py
import sys
from pathlib import Path

# Ensure src/ is on sys.path so `import parser` and `import codegen` work
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
import pandas as pd
import pytest

@pytest.fixture
def sample_df():
    """
    Simple synthetic OHLCV dataset:
    - close: 1..50 (increasing)
    - volume: 2,000,000 (constant, > 1,000,000)
    - open/high/low: identical to close for simplicity
    """
    n = 50
    close = list(range(1, n + 1))
    df = pd.DataFrame({
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": [2_000_000] * n
    })
    # give it a datetime index for realism
    df.index = pd.date_range("2025-01-01", periods=n, freq="D")
    return df
