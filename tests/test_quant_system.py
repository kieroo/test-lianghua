from quant_system import Backtester, MovingAverageCrossStrategy, compute_metrics, load_bars_from_csv


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
