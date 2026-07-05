"""Backtesting harness.

Replays history bar by bar, feeding the signal engine only the candles it
would have seen at the time (no look-ahead), and simulates the resulting
trades so a strategy's record can be judged on numbers instead of vibes.

v1 semantics (kept deliberately simple and honest):
- Long-only. A BUY signal opens a position at the NEXT bar's open; SELL/HOLD
  never open shorts.
- Exits, checked on every bar while in a position:
    1. stop hit   (bar low  <= stop)   -> exit at stop price
    2. target hit (bar high >= target) -> exit at target price
    If a bar spans both, the stop is assumed to fill first (pessimistic).
    3. SELL signal -> exit at next bar's open.
- A flat per-side fee (default 0.26%, Kraken taker) is charged on entry and
  exit so results aren't inflated by ignoring costs.
- One position at a time; position size is the whole (compounding) equity.

Results include buy-and-hold over the same window as the benchmark to beat.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .models import Candle
from .signals import analyze

WARMUP = 36  # bars before the first decision; MACD(12,26,9) needs 35
DEFAULT_FEE = 0.0026  # 0.26% per side (Kraken taker)


@dataclass
class Trade:
    entry_time: str
    entry: float
    exit_time: str = ""
    exit: float = 0.0
    reason: str = ""  # "stop" | "target" | "signal" | "end"
    stop: float = 0.0
    target: float = 0.0

    @property
    def pct(self) -> float:
        """Gross return of the trade in percent."""
        return (self.exit / self.entry - 1) * 100 if self.entry else 0.0


@dataclass
class BacktestResult:
    symbol: str
    bars: int
    start: str
    end: str
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    final_equity: float = 1.0
    buy_hold_return: float = 0.0
    fee: float = DEFAULT_FEE

    @property
    def total_return(self) -> float:
        return (self.final_equity - 1) * 100

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.pct > 0)
        return wins / len(self.trades) * 100

    @property
    def profit_factor(self) -> float:
        gains = sum(t.pct for t in self.trades if t.pct > 0)
        losses = -sum(t.pct for t in self.trades if t.pct < 0)
        if losses == 0:
            return float("inf") if gains > 0 else 0.0
        return gains / losses

    @property
    def max_drawdown(self) -> float:
        peak = -float("inf")
        worst = 0.0
        for eq in self.equity_curve:
            peak = max(peak, eq)
            worst = min(worst, (eq / peak - 1) * 100)
        return worst


def run(symbol: str, candles: List[Candle], fee: float = DEFAULT_FEE) -> BacktestResult:
    """Walk-forward simulate the signal engine over `candles` (oldest first)."""
    if len(candles) <= WARMUP + 1:
        raise ValueError(
            f"Need more than {WARMUP + 1} candles to backtest; got {len(candles)}"
        )

    result = BacktestResult(
        symbol=symbol,
        bars=len(candles),
        start=candles[0].timestamp,
        end=candles[-1].timestamp,
        fee=fee,
    )
    equity = 1.0
    in_pos = False
    trade: Optional[Trade] = None
    pending_entry = False
    pending_exit = False

    for i in range(WARMUP, len(candles) - 1):
        bar = candles[i]
        nxt = candles[i + 1]

        # --- resolve pending orders at this bar's open (placed last bar) ---
        if pending_entry and not in_pos:
            sig = analyze(symbol, candles[: i + 1])  # refresh levels at fill time
            trade = Trade(
                entry_time=bar.timestamp, entry=bar.open,
                stop=sig.stop, target=sig.target,
            )
            equity *= 1 - fee
            in_pos = True
            pending_entry = False
        elif pending_exit and in_pos and trade is not None:
            trade.exit_time, trade.exit, trade.reason = bar.timestamp, bar.open, "signal"
            equity *= (trade.exit / trade.entry) * (1 - fee)
            result.trades.append(trade)
            in_pos, trade, pending_exit = False, None, False

        # --- intrabar stop/target while positioned (stop first: pessimistic) ---
        # Gap-aware fills: a stop can't fill better than the open if the bar
        # opens below it, and a target can't fill worse than an open above it.
        if in_pos and trade is not None:
            if bar.low <= trade.stop:
                fill = min(trade.stop, bar.open)
                trade.exit_time, trade.exit, trade.reason = bar.timestamp, fill, "stop"
            elif bar.high >= trade.target:
                fill = max(trade.target, bar.open)
                trade.exit_time, trade.exit, trade.reason = bar.timestamp, fill, "target"
            if trade.reason:
                equity *= (trade.exit / trade.entry) * (1 - fee)
                result.trades.append(trade)
                in_pos, trade = False, None
                pending_exit = False

        # --- decide with only the data available at this bar's close ---
        sig = analyze(symbol, candles[: i + 1])
        if not in_pos and not pending_entry and sig.action == "BUY":
            pending_entry = True
        elif in_pos and sig.action == "SELL":
            pending_exit = True

        # mark equity to market
        mark = equity
        if in_pos and trade is not None:
            mark = equity * (bar.close / trade.entry)
        result.equity_curve.append(mark)
        _ = nxt  # next bar consumed on the following iteration

    # --- close any open position at the final bar's close ---
    last = candles[-1]
    if in_pos and trade is not None:
        trade.exit_time, trade.exit, trade.reason = last.timestamp, last.close, "end"
        equity *= (trade.exit / trade.entry) * (1 - fee)
        result.trades.append(trade)
    result.equity_curve.append(equity)
    result.final_equity = equity
    result.buy_hold_return = (last.close / candles[WARMUP].close - 1) * 100
    return result


def format_report(r: BacktestResult) -> str:
    lines = [
        "=" * 62,
        f"  BACKTEST  {r.symbol}  ({r.start[:10]} -> {r.end[:10]}, {r.bars} bars)",
        "=" * 62,
        "",
        f"  Strategy return   {r.total_return:+8.1f}%   (fees {r.fee*100:.2f}%/side included)",
        f"  Buy & hold        {r.buy_hold_return:+8.1f}%   (same window)",
        f"  Max drawdown      {r.max_drawdown:8.1f}%",
        f"  Trades            {r.n_trades:8d}",
        f"  Win rate          {r.win_rate:8.1f}%",
        f"  Profit factor     {r.profit_factor:8.2f}",
        "",
    ]
    if r.trades:
        lines.append("  Trades:")
        for t in r.trades:
            lines.append(
                f"    {t.entry_time[:10]} ${t.entry:>12,.2f} -> "
                f"{t.exit_time[:10]} ${t.exit:>12,.2f}  {t.pct:+7.2f}%  ({t.reason})"
            )
        lines.append("")
    verdict = (
        "Strategy beat buy & hold." if r.total_return > r.buy_hold_return
        else "Strategy did NOT beat buy & hold on this window."
    )
    lines += [
        "-" * 62,
        f"  {verdict}",
        "  Past performance does not guarantee future results.",
        "-" * 62,
    ]
    return "\n".join(lines)
