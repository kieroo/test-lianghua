from __future__ import annotations

import json
from urllib import error

from quant_system.live import BinanceMarketDataClient, BinanceSpotTrader, YahooUSMarketDataClient


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


def test_fetch_yahoo_us_bars():
    sample = {
        "chart": {
            "result": [
                {
                    "timestamp": [1710000000, 1710003600],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0, 101.0],
                                "high": [102.0, 103.0],
                                "low": [99.0, 100.0],
                                "close": [101.5, 102.5],
                                "volume": [1000000, 1200000],
                            }
                        ]
                    },
                }
            ]
        }
    }

    def fake_open(req, timeout=10.0):
        assert "finance/chart/AAPL" in req.full_url
        return _FakeResponse(sample)

    client = YahooUSMarketDataClient(_opener=fake_open)
    bars = client.fetch_klines("AAPL", interval="1h", limit=2)

    assert len(bars) == 2
    assert bars[0].open == 100.0
    assert bars[-1].close == 102.5


def test_fetch_yahoo_retries_on_429_then_success(monkeypatch):
    sample = {
        "chart": {
            "result": [
                {
                    "timestamp": [1710000000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0],
                                "high": [102.0],
                                "low": [99.0],
                                "close": [101.5],
                                "volume": [1000000],
                            }
                        ]
                    },
                }
            ]
        }
    }
    calls = {"count": 0}

    def fake_open(req, timeout=10.0):
        calls["count"] += 1
        if calls["count"] == 1:
            raise error.HTTPError(req.full_url, 429, "Too Many Requests", hdrs={"Retry-After": "0"}, fp=None)
        return _FakeResponse(sample)

    monkeypatch.setattr("quant_system.live.time.sleep", lambda _: None)
    client = YahooUSMarketDataClient(_opener=fake_open, max_retries=2)
    bars = client.fetch_klines("AAPL", interval="1h", limit=1)

    assert len(bars) == 1
    assert bars[0].close == 101.5
    assert calls["count"] == 2
