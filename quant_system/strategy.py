from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Literal

from .data import Bar

Signal = Literal[-1, 0, 1]


@dataclass
class MovingAverageCrossStrategy:
    """Classic MA cross strategy.

    - long_signal (1): short MA > long MA
    - flat_signal (0): short MA <= long MA
    """

    short_window: int = 5
    long_window: int = 20

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("window must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be less than long_window")
        self._short_prices: Deque[float] = deque(maxlen=self.short_window)
        self._long_prices: Deque[float] = deque(maxlen=self.long_window)

    def on_bar(self, bar: Bar) -> Signal:
        self._short_prices.append(bar.close)
        self._long_prices.append(bar.close)

        if len(self._long_prices) < self.long_window:
            return 0

        short_ma = sum(self._short_prices) / len(self._short_prices)
        long_ma = sum(self._long_prices) / len(self._long_prices)
        return 1 if short_ma > long_ma else 0
