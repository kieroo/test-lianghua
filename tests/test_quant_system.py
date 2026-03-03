from datetime import datetime

from quant_system import Bar, Backtester, MovingAverageCrossStrategy, compute_metrics, load_bars_from_csv


def test_load_and_backtest_sample_data():
    bars = load_bars_from_csv("data/sample_ohlcv.csv")
    strategy = MovingAverageCrossStrategy(short_window=3, long_window=5)
    backtester = Backtester(initial_capital=100000, fee_rate=0.001)

    result = backtester.run(bars, strategy)
    metrics = compute_metrics(result.equity_curve, result.returns)

    assert len(result.equity_curve) == len(bars)
    assert len(result.positions) == len(bars)
    assert result.equity_curve[-1] > 0
    assert metrics.max_drawdown <= 0


def test_invalid_strategy_windows():
    try:
        MovingAverageCrossStrategy(short_window=5, long_window=5)
    except ValueError as exc:
        assert "short_window" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_t1_disallow_same_day_sell():
    bars = [
        Bar(timestamp=datetime(2024, 1, 1, 9, 30), open=10, high=10, low=10, close=10, volume=1000),
        Bar(timestamp=datetime(2024, 1, 1, 10, 30), open=10, high=10, low=10, close=11, volume=1000),
        Bar(timestamp=datetime(2024, 1, 2, 9, 30), open=11, high=11, low=11, close=12, volume=1000),
    ]

    class _SignalStrategy:
        def __init__(self):
            self._signals = [1, 0, 0]
            self._i = 0

        def on_bar(self, bar):
            signal = self._signals[self._i]
            self._i += 1
            return signal

    t0_result = Backtester(initial_capital=1000, fee_rate=0.0, settlement="T+0").run(bars, _SignalStrategy())
    t1_result = Backtester(initial_capital=1000, fee_rate=0.0, settlement="T+1").run(bars, _SignalStrategy())

    assert t0_result.positions == [1, 0, 0]
    assert t1_result.positions == [1, 1, 0]
