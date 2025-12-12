# src/demo_parse.py

import sys
from pathlib import Path

# Force Python to import from the project root
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("USING PATH:", ROOT)

# Import parser
from parser import parse_dsl, parser as lark_parser
import json

# Test DSL examples
examples = [
    """
    ENTRY:
        close > SMA(close,20) AND volume > 1,000,000
    EXIT:
        RSI(close,14) < 30
    """,

    """
    ENTRY:
        close CROSSES_ABOVE SMA(close,50) AND volume > LASTWEEK(volume)
    EXIT:
        close < close[5]
    """,

    """
    ENTRY:
        price > SMA(close,10)
    """
]

for i, text in enumerate(examples, start=1):
    print(f"\n\n=== EXAMPLE {i} ===")
    
    # Step 1: Raw parse tree
    tree = lark_parser.parse(text)
    print("\n--- RAW TREE ---")
    print(tree.pretty())

    # Step 2: Build AST
    ast = parse_dsl(text)

    # Step 3: Print AST dictionary
    print("\n--- AST DICT ---")
    print(json.dumps(ast.to_dict(), indent=2))
