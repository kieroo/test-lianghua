from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_bars_from_csv(path: str | Path) -> List[Bar]:
    """Load OHLCV bars from a CSV file.

    CSV columns required: timestamp,open,high,low,close,volume
    timestamp format example: 2024-01-01 or 2024-01-01 09:30:00.
    """
    bars: List[Bar] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")

        for row in reader:
            ts = row["timestamp"].strip()
            try:
                timestamp = datetime.fromisoformat(ts)
            except ValueError as exc:
                raise ValueError(f"Invalid timestamp format: {ts}") from exc

            bars.append(
                Bar(
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )

    if not bars:
        raise ValueError("CSV has no data rows")

    return bars
