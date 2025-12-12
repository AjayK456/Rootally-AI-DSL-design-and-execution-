# src/codegen.py
import pandas as pd
import numpy as np
from .ast_nodes import ScriptAST, FieldNode, NumberNode, FunctionNode, CompareNode, BoolNode, CrossNode

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=1).mean()

def rsi(series: pd.Series, period: int) -> pd.Series:
    # Simple RSI implementation (wilders smoothing approx)
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(period, min_periods=1).mean()
    ma_down = down.rolling(period, min_periods=1).mean()
    rs = ma_up / (ma_down.replace(0, 1e-8))
    return 100 - (100 / (1 + rs))

def eval_node(node, df):
    """Return a pandas Series or scalar depending on node type."""
    if node is None:
        return pd.Series([False]*len(df), index=df.index)
    if isinstance(node, FieldNode):
        name = node.name.lower()
        return df[name]
    if isinstance(node, NumberNode):
        return node.value
    if isinstance(node, FunctionNode):
        name = node.name.lower()
        args = node.args
        # args may be AST nodes or numbers
        # common patterns: sma(close, N), rsi(close,N)
        if name == "sma":
            # expect args[0] field, args[1] number
            period = int(args[1].value) if isinstance(args[1], NumberNode) else int(args[1])
            # support if first arg is FieldNode or string
            series = eval_node(args[0], df)
            return sma(series, period)
        if name == "rsi":
            period = int(args[1].value) if isinstance(args[1], NumberNode) else int(args[1])
            series = eval_node(args[0], df)
            return rsi(series, period)
        # default: try name as column function (fallback)
        return df[name] if name in df.columns else pd.Series([False]*len(df), index=df.index)

    if isinstance(node, CompareNode):
        left = eval_node(node.left, df)
        right = eval_node(node.right, df)
        op = node.op
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        raise ValueError(f"Unknown compare op {op}")

    if isinstance(node, BoolNode):
        left = eval_node(node.left, df)
        right = eval_node(node.right, df)
        if node.op == "AND":
            return left & right
        else:
            return left | right

    if isinstance(node, CrossNode):
        left = eval_node(node.left, df)
        right = eval_node(node.right, df)
        if node.dir == "crosseS_above".lower() or node.dir == "crosses_above":
            # crosses above: previous left <= previous right and current left > current right
            prev_left = left.shift(1).fillna(method="bfill")
            prev_right = right.shift(1).fillna(method="bfill")
            return (prev_left <= prev_right) & (left > right)
        else:
            prev_left = left.shift(1).fillna(method="bfill")
            prev_right = right.shift(1).fillna(method="bfill")
            return (prev_left >= prev_right) & (left < right)

    raise ValueError(f"Unknown AST node: {node}")

def generate_signals(ast: ScriptAST, df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with boolean 'entry' and 'exit' series."""
    entry_series = eval_node(ast.entry, df) if ast.entry else pd.Series([False]*len(df), index=df.index)
    exit_series = eval_node(ast.exit, df) if ast.exit else pd.Series([False]*len(df), index=df.index)
    # ensure boolean Series
    entry_series = entry_series.fillna(False).astype(bool) if not isinstance(entry_series, (int, float)) else pd.Series([bool(entry_series)]*len(df), index=df.index)
    exit_series = exit_series.fillna(False).astype(bool) if not isinstance(exit_series, (int, float)) else pd.Series([bool(exit_series)]*len(df), index=df.index)
    signals = pd.DataFrame({"entry": entry_series, "exit": exit_series}, index=df.index)
    return signals
