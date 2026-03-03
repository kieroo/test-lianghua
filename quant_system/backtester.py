from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

from .data import Bar


class Strategy(Protocol):
    def on_bar(self, bar: Bar) -> int:
        ...


@dataclass
class BacktestResult:
    equity_curve: List[float]
    returns: List[float]
    positions: List[int]


@dataclass
class Backtester:
    initial_capital: float = 100_000.0
    fee_rate: float = 0.0005
    settlement: str = "T+0"

    def run(self, bars: List[Bar], strategy: Strategy) -> BacktestResult:
        if not bars:
            raise ValueError("bars cannot be empty")
        if self.settlement not in {"T+0", "T+1"}:
            raise ValueError("settlement must be T+0 or T+1")

        cash = self.initial_capital
        shares = 0.0
        last_buy_date = None
        prev_equity = self.initial_capital
        equity_curve: List[float] = []
        returns: List[float] = []
        positions: List[int] = []

        for bar in bars:
            target = strategy.on_bar(bar)

            if target == 1 and shares == 0:
                trade_value = cash
                fee = trade_value * self.fee_rate
                shares = (trade_value - fee) / bar.close
                cash = 0.0
                last_buy_date = bar.timestamp.date()
            elif target == 0 and shares > 0:
                if self.settlement == "T+1" and last_buy_date == bar.timestamp.date():
                    pass
                else:
                    trade_value = shares * bar.close
                    fee = trade_value * self.fee_rate
                    cash = trade_value - fee
                    shares = 0.0
                    last_buy_date = None

            equity = cash + shares * bar.close
            ret = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
            equity_curve.append(equity)
            returns.append(ret)
            positions.append(1 if shares > 0 else 0)
            prev_equity = equity

        return BacktestResult(equity_curve=equity_curve, returns=returns, positions=positions)
