# quick_run_backtest.py
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
import pandas as pd


from src.parser import parse_dsl
from src.codegen import generate_signal_function
from src.backtest import run_backtest


# ---------------------------
# 1) Example DSL strategy
# ---------------------------
dsl = """
ENTRY:
    close > SMA(close,20) AND volume > 1000000

EXIT:
    RSI(close,14) < 30
"""

# ---------------------------
# 2) PARSE → AST
# ---------------------------
ast = parse_dsl(dsl)
print("\n=== AST ===")
print(ast.to_dict())

# ---------------------------
# 3) Generate signals using codegen
# ---------------------------
df = pd.DataFrame({
    "open":[100,103,107,110,112,115,117,119,121,123,125]*3,
    "high":[x+2 for x in range(33)],
    "low":[x-2 for x in range(33)],
    "close":[100+i for i in range(33)],
    "volume":[900000,1200000,1500000]*11
})

signals = generate_signal_function(ast)(df)
print("\n=== SIGNALS ===")
print(signals)

# ---------------------------
# 4) Run Backtest
# ---------------------------
results = run_backtest(df, signals)

print("\n=== BACKTEST RESULTS ===")
for k, v in results.items():
    if k != "trades":
        print(f"{k}: {v}")

print("\n=== TRADES ===")
for t in results["trades"]:
    print(t)
