from quant_system.management import ManagementService


def test_update_strategy_and_run_backtest():
    service = ManagementService()
    service.update_strategy("ma", short_window=3, long_window=8)

    result = service.run_backtest(
        data_path="data/sample_ohlcv.csv",
        capital=100000,
        fee_rate=0.001,
        settlement="T+0",
    )

    assert result["data_points"] > 0
    assert result["final_equity"] > 0


def test_place_order_and_positions_flow():
    service = ManagementService(cash=1000)

    buy = service.place_order(symbol="btcusdt", side="buy", quantity=1, price=100)
    assert buy.side == "BUY"
    assert service.cash == 900
    assert len(service.list_positions()) == 1

    sell = service.place_order(symbol="BTCUSDT", side="SELL", quantity=0.4, price=150)
    assert sell.side == "SELL"
    positions = service.list_positions()
    assert len(positions) == 1
    assert positions[0].quantity == 0.6


def test_place_order_insufficient_position():
    service = ManagementService(cash=1000)
    service.place_order(symbol="AAPL", side="BUY", quantity=1, price=50)

    try:
        service.place_order(symbol="AAPL", side="SELL", quantity=2, price=60)
    except ValueError as exc:
        assert "insufficient position" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
