from __future__ import annotations

import json

from quant_system.live import BinanceMarketDataClient, BinanceSpotTrader


class _FakeResponse:
    def __init__(self, payload: object):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_fetch_klines_to_bars():
    sample = [
        [1710000000000, "100", "110", "90", "105", "1234", 1710000060000, "0", 0, "0", "0", "0"],
        [1710000060000, "105", "115", "95", "110", "456", 1710000120000, "0", 0, "0", "0", "0"],
    ]

    def fake_open(url, timeout=10.0):
        assert "symbol=BTCUSDT" in url
        return _FakeResponse(sample)

    client = BinanceMarketDataClient(_opener=fake_open)
    bars = client.fetch_klines("BTCUSDT", interval="1m", limit=2)

    assert len(bars) == 2
    assert bars[-1].close == 110.0
    assert bars[0].volume == 1234.0


def test_dry_run_market_order():
    trader = BinanceSpotTrader(api_key="k", api_secret="s", dry_run=True)
    result = trader.place_market_order("BTCUSDT", "BUY", 0.01)

    assert result.status == "DRY_RUN"
    assert result.symbol == "BTCUSDT"
    assert result.side == "BUY"
