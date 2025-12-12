# end_to_end.py
from src.nlp_to_dsl import nlp_to_dsl
from src.parser import parse_dsl
from src.codegen import generate_signals
from src.backtest import run_backtest
import pandas as pd
import numpy as np

DEFAULT_NL = "Buy when price closes above the 20-day moving average and volume is above 1M."

def demo_run(nl_input=None):
    nl = nl_input or DEFAULT_NL

    print("\nNatural Language Input:")
    print(nl)

    dsl = nlp_to_dsl(nl)
    print("\nGenerated DSL:")
    print(dsl)

    print("\nParsing DSL -> AST ...")
    ast = parse_dsl(dsl)
    print("\nParsed AST:")
    print(ast)

    # Generate sample data
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    np.random.seed(0)
    close = pd.Series(100 + np.cumsum(np.random.randn(len(dates))*2), index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([close, open_], axis=1).max(axis=1) + 1
    low = pd.concat([close, open_], axis=1).min(axis=1) - 1
    volume = pd.Series(500000 + np.random.randint(0, 500000, size=len(dates)), index=dates)

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    })

    signals = generate_signals(ast, df)
    print("\nSignals:")
    print(signals.tail(10))

    results = run_backtest(df, signals)
    print("\n=== BACKTEST RESULT ===")
    print(f"Total Return: {results['total_return']}")
    print(f"Max Drawdown: {results['max_drawdown']}")
    print(f"Trades: {results['number_of_trades']}")
    print("Trade Log:", results["trades"])


if __name__ == "__main__":
    user_input = input("Enter natural language rule (press Enter for default):\n> ")
    nl = user_input.strip() or DEFAULT_NL
    demo_run(nl)
