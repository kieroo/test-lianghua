from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .backtester import Backtester
from .data import load_bars_from_csv
from .metrics import compute_metrics
from .strategy import AdaptiveMultiFactorStrategy, MovingAverageCrossStrategy


@dataclass
class StrategyConfig:
    strategy_name: str = "adaptive"
    short_window: int = 5
    long_window: int = 20


@dataclass
class Position:
    symbol: str
    quantity: float
    avg_price: float


@dataclass
class Execution:
    symbol: str
    side: str
    quantity: float
    price: float


@dataclass
class ManagementService:
    strategy_config: StrategyConfig = field(default_factory=StrategyConfig)
    cash: float = 100000.0
    _positions: Dict[str, Position] = field(default_factory=dict)
    _executions: List[Execution] = field(default_factory=list)

    def update_strategy(self, strategy_name: str, short_window: int, long_window: int) -> StrategyConfig:
        if strategy_name not in {"ma", "adaptive"}:
            raise ValueError("strategy_name must be ma or adaptive")
        if short_window <= 0 or long_window <= 0:
            raise ValueError("window must be positive")
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

        self.strategy_config = StrategyConfig(
            strategy_name=strategy_name,
            short_window=short_window,
            long_window=long_window,
        )
        return self.strategy_config

    def run_backtest(self, data_path: str, capital: float, fee_rate: float, settlement: str) -> dict:
        bars = load_bars_from_csv(data_path)
        if self.strategy_config.strategy_name == "ma":
            strategy = MovingAverageCrossStrategy(
                short_window=self.strategy_config.short_window,
                long_window=self.strategy_config.long_window,
            )
        else:
            strategy = AdaptiveMultiFactorStrategy(
                short_window=self.strategy_config.short_window,
                long_window=self.strategy_config.long_window,
            )

        result = Backtester(initial_capital=capital, fee_rate=fee_rate, settlement=settlement).run(bars, strategy)
        metrics = compute_metrics(result.equity_curve, result.returns)
        return {
            "data_points": len(bars),
            "final_equity": result.equity_curve[-1],
            "positions": result.positions,
            "metrics": metrics,
        }

    def place_order(self, symbol: str, side: str, quantity: float, price: float) -> Execution:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if price <= 0:
            raise ValueError("price must be positive")

        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("symbol cannot be empty")

        if normalized_side == "BUY":
            cost = quantity * price
            if cost > self.cash:
                raise ValueError("insufficient cash")
            self.cash -= cost
            position = self._positions.get(symbol)
            if position is None:
                self._positions[symbol] = Position(symbol=symbol, quantity=quantity, avg_price=price)
            else:
                new_qty = position.quantity + quantity
                new_avg = (position.quantity * position.avg_price + quantity * price) / new_qty
                self._positions[symbol] = Position(symbol=symbol, quantity=new_qty, avg_price=new_avg)
        else:
            position = self._positions.get(symbol)
            if position is None or position.quantity < quantity:
                raise ValueError("insufficient position")
            self.cash += quantity * price
            remaining = position.quantity - quantity
            if remaining == 0:
                del self._positions[symbol]
            else:
                self._positions[symbol] = Position(symbol=symbol, quantity=remaining, avg_price=position.avg_price)

        execution = Execution(symbol=symbol, side=normalized_side, quantity=quantity, price=price)
        self._executions.append(execution)
        return execution

    def list_positions(self) -> List[Position]:
        return sorted(self._positions.values(), key=lambda p: p.symbol)

    def list_executions(self) -> List[Execution]:
        return list(self._executions)
