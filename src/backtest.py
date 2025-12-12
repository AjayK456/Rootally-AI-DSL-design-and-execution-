# src/backtest.py
from typing import Dict, Any, List
import pandas as pd
import numpy as np

def run_backtest(df: pd.DataFrame, signals: pd.DataFrame) -> Dict[str, Any]:
    """
    Very simple backtest:
    - enter when signals['entry'] True and not in position
    - exit when signals['exit'] True and in position
    - use close price for entry/exit
    """
    in_pos = False
    entry_price = None
    trades = []
    equity = 0
    equity_curve = []
    peak = 0
    trough = 0

    for idx in df.index:
        e = signals.loc[idx, "entry"]
        x = signals.loc[idx, "exit"]
        price = df.loc[idx, "close"]

        if not in_pos and e:
            in_pos = True
            entry_price = price
            entry_date = idx

        elif in_pos and x:
            exit_price = price
            exit_date = idx
            pnl = exit_price - entry_price
            trades.append({"entry_date": entry_date, "exit_date": exit_date,
                           "entry_price": float(entry_price), "exit_price": float(exit_price),
                           "pnl": float(pnl)})
            equity += pnl
            entry_price = None
            in_pos = False

        equity_curve.append(equity)

    # if still in position at end, close at last price
    if in_pos and entry_price is not None:
        exit_price = df.iloc[-1]["close"]
        exit_date = df.index[-1]
        pnl = exit_price - entry_price
        trades.append({"entry_date": entry_date, "exit_date": exit_date,
                       "entry_price": float(entry_price), "exit_price": float(exit_price),
                       "pnl": float(pnl)})
        equity += pnl
        equity_curve.append(equity)

    # metrics
    total_return = float(equity)
    number_of_trades = len(trades)
    # simple max drawdown on equity curve
    eq = np.array(equity_curve, dtype=float) if equity_curve else np.array([0.0])
    running_max = np.maximum.accumulate(eq)
    drawdowns = (eq - running_max)
    max_drawdown = float(drawdowns.min()) if drawdowns.size else 0.0

    return {
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "number_of_trades": number_of_trades,
        "equity_curve": equity_curve,
        "trades": trades
    }
