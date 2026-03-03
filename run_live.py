#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import time

from quant_system import AdaptiveMultiFactorStrategy, MovingAverageCrossStrategy
from quant_system.live import BinanceMarketDataClient, BinanceSpotTrader, YahooUSMarketDataClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Online market-data + trading loop")
    parser.add_argument("--market", choices=["crypto", "us"], default="crypto")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1m")
    parser.add_argument("--short-window", type=int, default=5)
    parser.add_argument("--long-window", type=int, default=20)
    parser.add_argument("--strategy", choices=["ma", "adaptive"], default="adaptive")
    parser.add_argument("--quantity", type=float, required=True, help="Order quantity per trade")
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=5, help="Loop count, -1 for infinite")
    parser.add_argument("--live", action="store_true", help="Actually place exchange orders")
    parser.add_argument("--settlement", choices=["T+0", "T+1"], default="T+0")
    args = parser.parse_args()

    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    if args.market == "us" and args.live:
        raise ValueError("US market mode currently supports dry-run only")

    if args.market == "crypto" and args.live and (not api_key or not api_secret):
        raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET are required when --live is enabled")

    data_client = BinanceMarketDataClient() if args.market == "crypto" else YahooUSMarketDataClient()
    trader = BinanceSpotTrader(api_key=api_key, api_secret=api_secret, dry_run=not args.live)
    if args.strategy == "ma":
        strategy = MovingAverageCrossStrategy(short_window=args.short_window, long_window=args.long_window)
    else:
        strategy = AdaptiveMultiFactorStrategy(short_window=args.short_window, long_window=args.long_window)

    current_position = 0
    last_buy_date = None
    idx = 0

    print(
        f"Start loop: market={args.market}, symbol={args.symbol}, interval={args.interval}, "
        f"live={args.live}, settlement={args.settlement}"
    )
    while args.iterations < 0 or idx < args.iterations:
        bars = data_client.fetch_klines(symbol=args.symbol, interval=args.interval, limit=args.long_window + 5)
        latest = bars[-1]
        signal = strategy.on_bar(latest)

        action = "HOLD"
        if signal == 1 and current_position == 0:
            order = trader.place_market_order(args.symbol, "BUY", args.quantity)
            current_position = 1
            last_buy_date = latest.timestamp.date()
            action = f"BUY -> {order.status}"
        elif signal == 0 and current_position == 1:
            if args.settlement == "T+1" and last_buy_date == latest.timestamp.date():
                action = "HOLD(T+1 lock)"
            else:
                order = trader.place_market_order(args.symbol, "SELL", args.quantity)
                current_position = 0
                last_buy_date = None
                action = f"SELL -> {order.status}"

        print(
            f"[{latest.timestamp.isoformat()}] close={latest.close:.4f} signal={signal} "
            f"position={current_position} action={action}"
        )

        idx += 1
        if args.iterations < 0 or idx < args.iterations:
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
