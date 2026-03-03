from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Callable, List
from urllib import error, parse, request

from .data import Bar


def _to_binance_interval(interval: str) -> str:
    mapping = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "1d": "1d",
    }
    if interval not in mapping:
        raise ValueError(f"Unsupported interval: {interval}")
    return mapping[interval]


@dataclass
class BinanceMarketDataClient:
    """Fetch online OHLCV data from Binance public REST API."""

    base_url: str = "https://api.binance.com"
    timeout: float = 10.0
    _opener: Callable[..., object] = request.urlopen

    def fetch_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> List[Bar]:
        if limit <= 0:
            raise ValueError("limit must be positive")

        params = parse.urlencode({
            "symbol": symbol.upper(),
            "interval": _to_binance_interval(interval),
            "limit": limit,
        })
        url = f"{self.base_url}/api/v3/klines?{params}"
        try:
            with self._opener(url, timeout=self.timeout) as resp:  # type: ignore[arg-type]
                payload = json.loads(resp.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Failed to fetch Binance klines: {exc}") from exc

        bars: List[Bar] = []
        for item in payload:
            open_time_ms = int(item[0])
            bars.append(
                Bar(
                    timestamp=datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc),
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    volume=float(item[5]),
                )
            )

        if not bars:
            raise ValueError("No kline data returned")
        return bars


@dataclass
class OrderResult:
    symbol: str
    side: str
    quantity: float
    status: str
    raw_response: dict


@dataclass
class BinanceSpotTrader:
    """Minimal Binance spot order client.

    Set `dry_run=True` for simulated online trading signals without placing orders.
    """

    api_key: str
    api_secret: str
    base_url: str = "https://api.binance.com"
    recv_window: int = 5000
    timeout: float = 10.0
    dry_run: bool = True
    _opener: Callable[..., object] = request.urlopen

    def place_market_order(self, symbol: str, side: str, quantity: float) -> OrderResult:
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        if self.dry_run:
            payload = {
                "symbol": symbol.upper(),
                "side": side,
                "executedQty": str(quantity),
                "status": "DRY_RUN",
            }
            return OrderResult(symbol=symbol.upper(), side=side, quantity=quantity, status="DRY_RUN", raw_response=payload)

        path = "/api/v3/order"
        params = {
            "symbol": symbol.upper(),
            "side": side,
            "type": "MARKET",
            "quantity": self._format_quantity(quantity),
            "recvWindow": str(self.recv_window),
            "timestamp": str(int(datetime.now(tz=timezone.utc).timestamp() * 1000)),
        }
        query = parse.urlencode(params)
        signature = hmac.new(self.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
        body = f"{query}&signature={signature}".encode("utf-8")

        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with self._opener(req, timeout=self.timeout) as resp:  # type: ignore[arg-type]
                result = json.loads(resp.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Failed to place Binance order: {exc}") from exc

        return OrderResult(
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            status=str(result.get("status", "UNKNOWN")),
            raw_response=result,
        )

    @staticmethod
    def _format_quantity(quantity: float) -> str:
        return f"{quantity:.8f}".rstrip("0").rstrip(".")
