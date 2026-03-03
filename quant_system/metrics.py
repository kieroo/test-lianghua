from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List


@dataclass
class PerformanceMetrics:
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float


def compute_metrics(equity_curve: List[float], returns: List[float], periods_per_year: int = 252) -> PerformanceMetrics:
    if not equity_curve:
        raise ValueError("equity_curve cannot be empty")

    total_return = equity_curve[-1] / equity_curve[0] - 1

    n = len(returns)
    avg_ret = sum(returns) / n if n else 0.0
    var = sum((r - avg_ret) ** 2 for r in returns) / (n - 1) if n > 1 else 0.0
    vol = sqrt(var) * sqrt(periods_per_year)
    ann_ret = (1 + total_return) ** (periods_per_year / max(n, 1)) - 1 if n > 0 else 0.0
    sharpe = (avg_ret * periods_per_year) / vol if vol > 0 else 0.0

    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = eq / peak - 1
        max_dd = min(max_dd, dd)

    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=ann_ret,
        annualized_volatility=vol,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
    )
