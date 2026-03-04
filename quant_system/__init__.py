"""Simple quantitative trading system package."""

from .backtester import Backtester
from .data import Bar, load_bars_from_csv
from .metrics import compute_metrics
from .strategy import AdaptiveMultiFactorStrategy, MovingAverageCrossStrategy
from .live import BinanceMarketDataClient, BinanceSpotTrader, OrderResult, YahooUSMarketDataClient
from .management import Execution, ManagementService, Position, StrategyConfig

__all__ = [
    "Bar",
    "Backtester",
    "MovingAverageCrossStrategy",
    "AdaptiveMultiFactorStrategy",
    "compute_metrics",
    "load_bars_from_csv",
    "BinanceMarketDataClient",
    "BinanceSpotTrader",
    "YahooUSMarketDataClient",
    "OrderResult",
    "StrategyConfig",
    "Position",
    "Execution",
    "ManagementService",
]
