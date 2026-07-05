# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## What this project is

**meltmarketexchange** is an AI-assisted trading assistant. It fetches market
data from **Kraken**, computes technical indicators, and produces a **morning
briefing** of the day's plays: ranked BUY / SELL / HOLD signals with confidence,
entry/stop/target levels, and a plain-English rationale.

It is **decision support, not financial advice**, and it is **read-only** today
(v0.1) — no live order execution. Keep it that way until an execution layer is
explicitly, deliberately added with paper-trading defaults and safeguards.

## Language & tooling

- **Language:** Python (>= 3.10)
- **Runtime dependencies:** none — pure standard library (keep it that way unless
  there's a strong reason; surface any new dependency before adding it)
- **Dev dependency:** `pytest`
- **Packaging:** `pyproject.toml` (setuptools, `src/` layout), console script `melt`

## Repository layout

```
pyproject.toml            Packaging, console script, pytest config
README.md                 User-facing overview and usage
CLAUDE.md                 This file
src/melt/
  __init__.py             Package metadata / docstring
  models.py               Candle and Signal dataclasses (shared types)
  indicators.py           SMA, EMA, RSI, MACD, ROC, ATR (pure-Python math)
  signals.py              Weighted rule engine -> Signal (action/confidence/risk)
  kraken.py               Kraken public OHLC feed + offline snapshot loader
  briefing.py             Watchlist scan + morning-briefing text formatting
  backtest.py             Walk-forward backtester (no look-ahead, fees, gap fills)
  cli.py                  argparse entry point: morning / scan / demo / backtest
  data/btc_snapshot.json  Real BTC/USD daily snapshot for offline demo & tests
  data/btc_history.json   Real BTC/USD 1-year daily history for offline backtests
tests/
  test_indicators.py      Indicator math
  test_signals.py         Signal engine + snapshot
  test_backtest.py        Backtest engine mechanics + real-history run
```

## Architecture notes

- **Data flow:** `kraken.fetch_ohlc()` → `List[Candle]` → `signals.analyze()` →
  `Signal` → `briefing.format_briefing()` → text. The feed is the only I/O
  boundary; everything downstream is pure and easily testable.
- **Signal engine is intentionally transparent.** `signals.WEIGHTS` maps each
  check (trend / MACD / RSI / momentum) to a contribution; the summed score maps
  to BUY/SELL/HOLD via `BUY_THRESHOLD` / `SELL_THRESHOLD`. No black box — every
  play must be explainable and back-testable. Tune weights/thresholds here.
- **Risk levels come from ATR** (`ATR_STOP_MULT`, `REWARD_MULT`), so stops adapt
  to volatility rather than being fixed percentages.
- **Indicators return `None`** when there isn't enough history; `analyze()` and
  the briefing degrade gracefully rather than crash. Preserve that.
- **Symbols** are friendly tickers (`BTC`, `ETH`); `kraken.PAIR_ALIASES` maps them
  to Kraken pair names (`XBTUSD`, ...). Extend the alias table for new markets.

## Development commands

```bash
# Install (editable) with dev tools
pip install -e ".[dev]"

# Run the offline demo on bundled real data (no network needed)
python -m melt.cli demo        # or: melt demo

# Live morning briefing (needs outbound access to api.kraken.com)
melt morning --watchlist BTC,ETH,SOL --interval 1d

# Backtest on bundled real 1-year BTC history (offline)
python -m melt.cli backtest --offline

# Tests
pytest -q
```

Note: sandboxed CI/agent environments may block outbound HTTPS to
`api.kraken.com`. Use `melt demo` and the tests (both offline) to verify logic
there; live commands need real network access.

## Conventions

- Keep the runtime dependency-free where practical.
- New indicators go in `indicators.py` with a matching test in
  `tests/test_indicators.py`; keep signatures `(values, period)`-style and return
  `None` on insufficient data.
- New signal inputs go through `signals.WEIGHTS` so scoring stays transparent and
  the weights sum to a sane range.
- Judge any strategy/weight change with `melt backtest --offline` and report the
  before/after numbers; never claim improvement without them. The backtester must
  stay look-ahead-free: decisions use only `candles[:i+1]`, fills happen at the
  next bar, gapped stops/targets fill at the worse price.
- Any change touching order placement / real money must default to paper trading
  and be gated behind an explicit opt-in. Do not add live-trading code silently.
- Update this file and `README.md` in the same change when you alter structure,
  commands, or conventions.

## Git workflow

- **Default branch:** `main`. Do not commit directly to `main`.
- Develop on a feature branch; push with `git push -u origin <branch-name>`.
- After pushing, open a **draft** PR if no open PR already exists for the branch.
- Write commit messages that explain the *why*, not just the *what*.
- There is no PR template yet; if you add one, place it at
  `.github/pull_request_template.md`.

## Roadmap (keep current as items land)

- [x] Backtesting harness to validate strategies on history
- [ ] Stocks data feed (alongside Kraken crypto)
- [ ] Live order execution via Kraken private API (opt-in, paper-first)
- [ ] Position sizing / portfolio risk model
- [ ] Config file for watchlist, weights, and thresholds
- [ ] CI pipeline (`.github/workflows/`) running `pytest`

## Notes for AI assistants

- Verify claims against the working tree before stating them.
- Do not fabricate market data. The bundled snapshot is real historical data;
  keep it that way, and label any synthetic fixtures clearly as synthetic.
- Do not overpromise predictive power. Frame output as probabilistic decision
  support with explicit risk, never guaranteed returns.
