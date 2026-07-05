# meltmarketexchange

An AI-assisted trading assistant. It pulls market data from **Kraken**, runs
technical + statistical analysis, and every morning gives you a briefing of the
day's **plays** — ranked BUY / SELL / HOLD calls with confidence, entry, stop,
target, and a plain-English rationale for each.

> **Not financial advice.** Signals are decision support. Start in paper-trading
> mode and size every position to its stop. Markets cannot be reliably
> "predicted" — the edge here is disciplined analysis and risk management, not
> magic.

## Status

v0.1 — **read-only analysis** (no live order execution yet).

- ✅ Kraken public OHLC data feed (no API key needed)
- ✅ Indicators: SMA, EMA, RSI, MACD, ROC momentum, ATR
- ✅ Signal engine: transparent weighted rules → BUY/SELL/HOLD + confidence + ATR-based risk levels
- ✅ Morning briefing over a watchlist (crypto majors by default)
- ✅ Offline `demo` on a bundled real BTC/USD snapshot
- ✅ Backtesting harness: walk-forward, no look-ahead, fees + gap-aware fills,
  benchmarked against buy & hold (bundled real 1-year BTC history for offline runs)
- ⏳ Stocks feed (planned)
- ⏳ Live order execution via Kraken private API (planned, opt-in)

## Install

```bash
pip install -e ".[dev]"   # editable install + pytest
```

Runtime has **no third-party dependencies** (pure standard library).

## Usage

```bash
# Offline demo on bundled real BTC data — works with no network
melt demo

# Live morning briefing over the default crypto watchlist (needs internet)
melt morning

# Custom watchlist / interval
melt morning --watchlist BTC,ETH,SOL,LINK --interval 4h

# Deep-dive a single symbol
melt scan ETH

# Backtest the strategy on a year of bundled real BTC history (offline)
melt backtest --offline

# Backtest any symbol on live Kraken history
melt backtest ETH --interval 4h
```

Backtests charge 0.26%/side fees (Kraken taker) by default and report win
rate, profit factor, max drawdown, and a buy-and-hold benchmark. Judge every
strategy change against `melt backtest` before trusting it with money.

Example (`melt demo`):

```
  ― HOLD  BTC     $62,698.42     conf   16%   R:R 2.0
            - Downtrend: 10-MA 60859.13 below 20-MA 61301.51
            - RSI 48 - neutral
            - 10-bar momentum +4.9%
```

## Run the morning briefing automatically

On macOS/Linux, add a cron entry (7:30am daily):

```
30 7 * * *  cd /path/to/meltmarketexchange && melt morning >> ~/melt-briefing.log 2>&1
```

## Tests

```bash
pytest -q
```

See [CLAUDE.md](CLAUDE.md) for architecture and contribution conventions.
