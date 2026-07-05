"""Core data structures shared across the assistant."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Candle:
    """A single OHLCV bar."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    """The assistant's read on one instrument at one point in time."""

    symbol: str
    action: str  # "BUY", "SELL", or "HOLD"
    confidence: float  # 0.0 - 1.0
    score: float  # raw weighted score, negative = bearish, positive = bullish
    price: float
    entry: float
    stop: float
    target: float
    rationale: List[str] = field(default_factory=list)

    @property
    def risk_reward(self) -> float:
        risk = abs(self.entry - self.stop)
        reward = abs(self.target - self.entry)
        return round(reward / risk, 2) if risk else 0.0
