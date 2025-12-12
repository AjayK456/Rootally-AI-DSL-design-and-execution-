import sys
import os
sys.path.append(os.path.abspath("C:/Users/kulan/Desktop/Ajay/Projects/Rootally AI/src"))
from parser import parse_dsl
from codegen import generate_signal_function
import pandas as pd
from pathlib import Path
import sys

# Ensure imports work
sys.path.append(str(Path(__file__).resolve().parent))

# EXAMPLE DSL
dsl = """
ENTRY:
close > SMA(close,20) AND volume > 1000000

EXIT:
RSI(close,14) < 30
"""

# Parse DSL → AST
ast = parse_dsl(dsl)

print("\n=== AST OUTPUT ===")
print(ast.to_dict())

# Build dummy dataframe
df = pd.DataFrame({
    "close": list(range(1, 31)),
    "volume": [500000]*15 + [1500000]*15
})

# Generate signals
signals = generate_signal_function(ast, df)

print("\n=== SIGNAL OUTPUT ===")
print(signals)
