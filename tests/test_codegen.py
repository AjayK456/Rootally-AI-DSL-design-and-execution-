#test_codegen.py
import pandas as pd
import pytest
from parser import parse_dsl

# try importing both possible APIs in codegen
try:
    from codegen import generate_signal_function
    codegen_callable = True
except Exception:
    # fallback: codegen may export generate_signals_from_ast(ast, df)
    from codegen import generate_signals_from_ast
    codegen_callable = False

DSL = """
ENTRY:
close > SMA(close,20) AND volume > 1000000
EXIT:
RSI(close,14) < 30
"""

def test_codegen_runs_and_signals(sample_df):
    ast = parse_dsl(DSL)

    if codegen_callable:
        # generator returns a function
        fn = generate_signal_function(ast)
        signals = fn(sample_df)
    else:
        # direct API: function requires both ast and df
        signals = generate_signals_from_ast(ast, sample_df)

    assert isinstance(signals, pd.DataFrame)
    assert "entry" in signals.columns and "exit" in signals.columns

    # Entry should be False until index 19 (first full 20-window),
    # and True from index 19 onward for this synthetic increasing series.
    assert signals["entry"].iloc[0:19].sum() == 0
    assert signals["entry"].iloc[19:].sum() >= 1

    # Exit should be mostly False for increasing series (RSI not <30)
    assert signals["exit"].sum() == 0
