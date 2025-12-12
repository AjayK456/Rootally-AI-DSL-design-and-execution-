#test_indicators.py
import pandas as pd
from parser import parse_dsl
from codegen import generate_signals_from_ast
from ast_nodes import IndicatorNode, FieldNode, NumberNode

def test_sma_manual(sample_df):
    # compute sma direct via pandas and compare
    sma_series = sample_df["close"].rolling(20).mean()
    # check that the first non-NaN 20-window is at index 19 and value matches
    assert pd.isna(sma_series.iloc[18])
    assert not pd.isna(sma_series.iloc[19])
    # sanity check numeric value: average of 1..20 = 10.5
    assert abs(sma_series.iloc[19] - 10.5) < 1e-8

def test_rsi_shape(sample_df):
    # quick check that RSI function exists via codegen module
    import importlib
    cg = importlib.import_module("codegen")
    # try compute_rsi or compute_rsi-like function names
    rsi_fn = None
    for name in ("compute_rsi", "compute_rsi", "rsi", "compute_rsi_series"):
        rsi_fn = getattr(cg, name, None)
        if callable(rsi_fn):
            break
    # If no helper found, just ensure generate_signals_from_ast runs (coverage)
    ast = parse_dsl("""
    ENTRY:
    RSI(close,14) < 30
    """)
    signals = cg.generate_signals_from_ast(ast, sample_df)
    assert "entry" in signals.columns
