# tests/test_parser.py
import json
from parser import parse_dsl

EX1 = """
ENTRY:
close > SMA(close,20) AND volume > 1000000
EXIT:
RSI(close,14) < 30
"""

EX2 = """
ENTRY:
close CROSSES_ABOVE SMA(close,50) AND volume > LASTWEEK(volume)
EXIT:
close < close[5]
"""

EX3 = """
ENTRY:
price > SMA(close,10)
"""

def _validate_ast_dict(d):
    assert isinstance(d, dict)
    assert "entry" in d and "exit" in d
    # entry and exit can be None for some examples; ensure structure type when present
    if d["entry"] is not None:
        assert isinstance(d["entry"], dict)
        assert "type" in d["entry"]
    if d["exit"] is not None:
        assert isinstance(d["exit"], dict)
        assert "type" in d["exit"]

def test_example_1_ast():
    ast = parse_dsl(EX1)
    d = ast.to_dict()
    _validate_ast_dict(d)
    # entry should be bool type combining two comparisons
    assert d["entry"]["type"] == "bool"
    # exit should be a compare (rsi < 30)
    assert d["exit"]["type"] == "compare" or d["exit"]["type"] == "bool"

def test_example_2_ast():
    ast = parse_dsl(EX2)
    d = ast.to_dict()
    _validate_ast_dict(d)
    # entry should contain a cross node somewhere (type 'cross')
    # do a shallow search for 'cross' in the dict
    s = json.dumps(d).lower()
    assert "cross" in s

def test_example_3_ast():
    ast = parse_dsl(EX3)
    d = ast.to_dict()
    _validate_ast_dict(d)
    # price should be normalized to close in parser output
    # check that left field name in compare is 'close'
    assert d["entry"]["left"]["name"] == "close"
