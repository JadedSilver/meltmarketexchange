"""Technical indicators.

Pure-Python implementations (no numpy/pandas) so the assistant runs anywhere
with a stock interpreter. Each function takes a list of floats (oldest first)
and returns either a single latest value or a list aligned to the input.
"""
from __future__ import annotations

from typing import List, Optional


def sma(values: List[float], period: int) -> Optional[float]:
    """Simple moving average of the last `period` values."""
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period


def ema_series(values: List[float], period: int) -> List[float]:
    """Exponential moving average series (same length as input once seeded)."""
    if not values or period <= 0:
        return []
    k = 2 / (period + 1)
    out: List[float] = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def ema(values: List[float], period: int) -> Optional[float]:
    series = ema_series(values, period)
    return series[-1] if series else None


def rsi(values: List[float], period: int = 14) -> Optional[float]:
    """Wilder's Relative Strength Index for the latest bar."""
    if len(values) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    # Seed with the first `period` changes.
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    # Wilder smoothing across the remaining changes.
    for i in range(period + 1, len(values)):
        change = values[i] - values[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Return (macd_line, signal_line, histogram) for the latest bar."""
    if len(values) < slow + signal:
        return None, None, None
    fast_ema = ema_series(values, fast)
    slow_ema = ema_series(values, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema_series(macd_line, signal)
    hist = macd_line[-1] - signal_line[-1]
    return macd_line[-1], signal_line[-1], hist


def roc(values: List[float], period: int = 10) -> Optional[float]:
    """Rate of change (%) over `period` bars."""
    if len(values) < period + 1 or values[-period - 1] == 0:
        return None
    return (values[-1] / values[-period - 1] - 1) * 100


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    """Average True Range (Wilder) for the latest bar."""
    n = len(closes)
    if n < period + 1 or len(highs) != n or len(lows) != n:
        return None
    trs: List[float] = []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    atr_val = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr_val = (atr_val * (period - 1) + tr) / period
    return atr_val
