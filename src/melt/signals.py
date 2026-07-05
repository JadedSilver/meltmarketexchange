"""Signal engine.

Combines several indicators into a single weighted score, then maps that score
to a BUY / SELL / HOLD call with a confidence, a plain-English rationale, and
ATR-based stop/target levels. This is deliberately transparent rule-based logic
-- no black box -- so every play can be explained and back-tested.
"""
from __future__ import annotations

from typing import List

from . import indicators as ind
from .models import Candle, Signal

# How much each check contributes to the score. Tune these as strategies evolve.
WEIGHTS = {
    "trend": 0.35,      # fast SMA above/below slow SMA
    "macd": 0.25,       # MACD histogram sign
    "rsi": 0.20,        # oversold / overbought
    "momentum": 0.20,   # rate of change
}

BUY_THRESHOLD = 0.30
SELL_THRESHOLD = -0.30
ATR_STOP_MULT = 1.5
REWARD_MULT = 2.0  # target = 2x the risk (2R)


def analyze(symbol: str, candles: List[Candle]) -> Signal:
    """Produce a Signal for one instrument from its OHLCV history."""
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    price = closes[-1]

    score = 0.0
    rationale: List[str] = []

    # --- Trend: fast vs slow moving average ---
    fast = ind.sma(closes, 10)
    slow = ind.sma(closes, 20) or ind.sma(closes, min(len(closes), 20))
    if fast is not None and slow is not None:
        if fast > slow:
            score += WEIGHTS["trend"]
            rationale.append(f"Uptrend: 10-MA {fast:.2f} above 20-MA {slow:.2f}")
        else:
            score -= WEIGHTS["trend"]
            rationale.append(f"Downtrend: 10-MA {fast:.2f} below 20-MA {slow:.2f}")

    # --- MACD histogram ---
    _, _, hist = ind.macd(closes)
    if hist is not None:
        if hist > 0:
            score += WEIGHTS["macd"]
            rationale.append(f"MACD histogram positive ({hist:+.2f}) - bullish momentum")
        else:
            score -= WEIGHTS["macd"]
            rationale.append(f"MACD histogram negative ({hist:+.2f}) - bearish momentum")

    # --- RSI (mean reversion) ---
    r = ind.rsi(closes)
    if r is not None:
        if r < 30:
            score += WEIGHTS["rsi"]
            rationale.append(f"RSI {r:.0f} - oversold, bounce likely")
        elif r > 70:
            score -= WEIGHTS["rsi"]
            rationale.append(f"RSI {r:.0f} - overbought, pullback risk")
        else:
            rationale.append(f"RSI {r:.0f} - neutral")

    # --- Momentum (rate of change) ---
    m = ind.roc(closes, 10)
    if m is not None:
        if m > 0:
            score += WEIGHTS["momentum"] * min(m / 5, 1)
            rationale.append(f"10-bar momentum {m:+.1f}%")
        else:
            score += WEIGHTS["momentum"] * max(m / 5, -1)
            rationale.append(f"10-bar momentum {m:+.1f}%")

    # --- Decide action + confidence ---
    if score >= BUY_THRESHOLD:
        action = "BUY"
    elif score <= SELL_THRESHOLD:
        action = "SELL"
    else:
        action = "HOLD"
    confidence = min(abs(score), 1.0)

    # --- Risk levels from ATR ---
    a = ind.atr(highs, lows, closes) or (price * 0.02)  # fallback 2% band
    if action == "SELL":
        stop = price + ATR_STOP_MULT * a
        target = price - ATR_STOP_MULT * REWARD_MULT * a
    else:  # BUY or HOLD framed as a long setup
        stop = price - ATR_STOP_MULT * a
        target = price + ATR_STOP_MULT * REWARD_MULT * a

    return Signal(
        symbol=symbol,
        action=action,
        confidence=round(confidence, 3),
        score=round(score, 3),
        price=round(price, 2),
        entry=round(price, 2),
        stop=round(stop, 2),
        target=round(target, 2),
        rationale=rationale,
    )
