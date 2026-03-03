#!/usr/bin/env python3
from __future__ import annotations

import argparse

from quant_system import (
    AdaptiveMultiFactorStrategy,
    Backtester,
    MovingAverageCrossStrategy,
    compute_metrics,
    load_bars_from_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple quant backtest runner")
    parser.add_argument("--data", required=True, help="CSV path with OHLCV data")
    parser.add_argument("--short-window", type=int, default=5)
    parser.add_argument("--long-window", type=int, default=20)
    parser.add_argument("--strategy", choices=["ma", "adaptive"], default="adaptive")
    parser.add_argument("--capital", type=float, default=100000)
    parser.add_argument("--fee-rate", type=float, default=0.0005)
    parser.add_argument("--settlement", choices=["T+0", "T+1"], default="T+0")
    args = parser.parse_args()

    bars = load_bars_from_csv(args.data)
    if args.strategy == "ma":
        strategy = MovingAverageCrossStrategy(short_window=args.short_window, long_window=args.long_window)
    else:
        strategy = AdaptiveMultiFactorStrategy(short_window=args.short_window, long_window=args.long_window)
    backtester = Backtester(initial_capital=args.capital, fee_rate=args.fee_rate, settlement=args.settlement)
    result = backtester.run(bars, strategy)
    m = compute_metrics(result.equity_curve, result.returns)

    print("=== Backtest Result ===")
    print(f"Data points        : {len(bars)}")
    print(f"Final equity       : {result.equity_curve[-1]:.2f}")
    print(f"Total return       : {m.total_return:.2%}")
    print(f"Annualized return  : {m.annualized_return:.2%}")
    print(f"Annualized vol     : {m.annualized_volatility:.2%}")
    print(f"Sharpe ratio       : {m.sharpe_ratio:.3f}")
    print(f"Max drawdown       : {m.max_drawdown:.2%}")


if __name__ == "__main__":
    main()
