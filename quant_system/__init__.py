"""Simple quantitative trading system package."""

from .backtester import Backtester
from .data import Bar, load_bars_from_csv
from .metrics import compute_metrics
from .strategy import MovingAverageCrossStrategy

__all__ = [
    "Bar",
    "Backtester",
    "MovingAverageCrossStrategy",
    "compute_metrics",
    "load_bars_from_csv",
]
