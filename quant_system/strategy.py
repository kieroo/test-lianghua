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


@dataclass
class AdaptiveMultiFactorStrategy:
    """More robust long/flat strategy with trend + momentum + risk filters.

    Design goals:
    - Reduce false breakouts in noisy sideways markets.
    - Keep rules transparent and computationally light.

    Signal logic:
    - Build a confidence score using:
      1) Trend strength (short MA vs long MA)
      2) Price momentum (recent return)
      3) RSI-like oscillator (avoid overbought chasing)
      4) Volatility regime filter (avoid abnormally volatile bars)
    - Use different enter/exit thresholds (hysteresis) to avoid frequent flips.
    """

    short_window: int = 5
    long_window: int = 20
    momentum_window: int = 5
    rsi_window: int = 10
    vol_window: int = 10
    enter_threshold: float = 0.52
    exit_threshold: float = 0.38
    max_acceptable_volatility: float = 0.06

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("window must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be less than long_window")
        if self.momentum_window <= 0 or self.rsi_window <= 1 or self.vol_window <= 1:
            raise ValueError("momentum/rsi/vol windows must be valid positive integers")
        if not 0 <= self.exit_threshold < self.enter_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= exit < enter <= 1")

        # Keep factor windows practical for short-cycle configs (e.g., long_window=8).
        self._effective_momentum_window = min(self.momentum_window, self.long_window)
        self._effective_rsi_window = min(self.rsi_window, self.long_window)
        self._effective_vol_window = min(self.vol_window, self.long_window)

        maxlen = max(
            self.long_window,
            self._effective_momentum_window + 1,
            self._effective_rsi_window + 1,
            self._effective_vol_window + 1,
        )
        self._prices: Deque[float] = deque(maxlen=maxlen)
        self._position = 0

    def on_bar(self, bar: Bar) -> Signal:
        self._prices.append(bar.close)
        min_ready = max(
            self.long_window,
            self._effective_momentum_window + 1,
            self._effective_rsi_window + 1,
            self._effective_vol_window + 1,
        )
        if len(self._prices) < min_ready:
            return 0

        prices = list(self._prices)
        score = self._build_confidence_score(prices)

        if self._position == 0 and score >= self.enter_threshold:
            self._position = 1
        elif self._position == 1 and score <= self.exit_threshold:
            self._position = 0

        return self._position

    def _build_confidence_score(self, prices: list[float]) -> float:
        trend_component = self._trend_score(prices)
        momentum_component = self._momentum_score(prices)
        rsi_component = self._rsi_score(prices)
        volatility_component = self._volatility_score(prices)

        # Weighted sum: trend + momentum as core alpha, RSI/volatility as risk adjustment.
        return (
            0.40 * trend_component
            + 0.30 * momentum_component
            + 0.15 * rsi_component
            + 0.15 * volatility_component
        )

    def _trend_score(self, prices: list[float]) -> float:
        short_ma = sum(prices[-self.short_window :]) / self.short_window
        long_ma = sum(prices[-self.long_window :]) / self.long_window
        # Normalize MA distance to [0, 1].
        distance = (short_ma - long_ma) / long_ma if long_ma else 0.0
        return max(0.0, min(1.0, 0.5 + distance * 15.0))

    def _momentum_score(self, prices: list[float]) -> float:
        previous = prices[-self._effective_momentum_window - 1]
        if previous <= 0:
            return 0.0
        momentum = (prices[-1] - previous) / previous
        return max(0.0, min(1.0, 0.5 + momentum * 10.0))

    def _rsi_score(self, prices: list[float]) -> float:
        gains = 0.0
        losses = 0.0
        start = len(prices) - self._effective_rsi_window
        for i in range(start, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains += change
            else:
                losses -= change

        avg_gain = gains / self._effective_rsi_window
        avg_loss = losses / self._effective_rsi_window

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        # Prefer moderate bullish zone, penalize overbought/oversold extremes.
        if 45 <= rsi <= 65:
            return 1.0
        if 35 <= rsi < 45 or 65 < rsi <= 75:
            return 0.6
        if 25 <= rsi < 35 or 75 < rsi <= 85:
            return 0.3
        return 0.0

    def _volatility_score(self, prices: list[float]) -> float:
        returns = []
        for i in range(len(prices) - self._effective_vol_window, len(prices)):
            prev = prices[i - 1]
            if prev <= 0:
                continue
            returns.append((prices[i] - prev) / prev)

        if not returns:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        vol = variance**0.5

        if vol >= self.max_acceptable_volatility:
            return 0.0
        # Lower volatility -> higher confidence
        return max(0.0, min(1.0, 1.0 - vol / self.max_acceptable_volatility))
