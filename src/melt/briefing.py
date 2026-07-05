"""Morning briefing: scan a watchlist and rank the day's plays."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, List

from .models import Candle, Signal
from .signals import analyze

# Default things to watch. Extend or override via the CLI / config later.
DEFAULT_WATCHLIST = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "DOGE"]


def scan(watchlist: List[str], fetch: Callable[[str], List[Candle]]) -> List[Signal]:
    """Run the signal engine over every symbol; skip ones that error out."""
    signals: List[Signal] = []
    for symbol in watchlist:
        try:
            candles = fetch(symbol)
            if len(candles) < 15:
                continue
            signals.append(analyze(symbol, candles))
        except Exception as exc:  # keep the briefing resilient to one bad feed
            print(f"  ! skipped {symbol}: {exc}")
    # Strongest conviction first.
    signals.sort(key=lambda s: s.confidence, reverse=True)
    return signals


def format_briefing(signals: List[Signal]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "=" * 62,
        f"  MELT MARKET EXCHANGE  --  MORNING BRIEFING  ({now})",
        "=" * 62,
        "",
    ]
    actionable = [s for s in signals if s.action != "HOLD"]
    if actionable:
        lines.append(f"TODAY'S PLAYS ({len(actionable)} actionable of {len(signals)} scanned):")
    else:
        lines.append("No high-conviction plays today -- everything reads HOLD.")
    lines.append("")

    for s in signals:
        tag = {"BUY": "▲ BUY ", "SELL": "▼ SELL", "HOLD": "― HOLD"}[s.action]
        lines.append(
            f"  {tag}  {s.symbol:<6}  ${s.price:<12,.2f}  "
            f"conf {s.confidence*100:>4.0f}%   R:R {s.risk_reward}"
        )
        if s.action != "HOLD":
            lines.append(
                f"          entry ${s.entry:,.2f}  |  stop ${s.stop:,.2f}  |  target ${s.target:,.2f}"
            )
        for reason in s.rationale:
            lines.append(f"            - {reason}")
        lines.append("")

    lines.append("-" * 62)
    lines.append("Signals are decision support, not financial advice. Paper-trade")
    lines.append("first. Always size positions to the stop, never risk-of-ruin.")
    lines.append("-" * 62)
    return "\n".join(lines)
