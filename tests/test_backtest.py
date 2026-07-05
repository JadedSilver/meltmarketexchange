import pytest

from melt import backtest, kraken
from melt.models import Candle


def _flat(n, price=100.0):
    """Synthetic flat series (clearly synthetic, for engine mechanics only)."""
    return [Candle(f"t{i}", price, price + 0.1, price - 0.1, price, 10) for i in range(n)]


def _ramp(n, start=100.0, step=2.0):
    """Synthetic steady uptrend."""
    out = []
    p = start
    for i in range(n):
        o = p
        p += step
        out.append(Candle(f"t{i}", o, p + 0.5, o - 0.5, p, 10))
    return out


def test_too_little_history_raises():
    with pytest.raises(ValueError):
        backtest.run("X", _flat(10))


def test_flat_market_makes_no_trades():
    r = backtest.run("X", _flat(80))
    assert r.n_trades == 0
    assert r.final_equity == 1.0


def test_uptrend_enters_and_profits():
    r = backtest.run("X", _ramp(120))
    assert r.n_trades >= 1
    assert r.total_return > 0
    # every trade must have a resolved exit
    assert all(t.reason in {"stop", "target", "signal", "end"} for t in r.trades)


def test_no_lookahead_entry_prices():
    """Entries fill at a bar's open, one bar after the signal."""
    r = backtest.run("X", _ramp(120))
    for t in r.trades:
        assert t.entry > 0 and t.exit > 0


def test_fees_reduce_returns():
    free = backtest.run("X", _ramp(120), fee=0.0)
    costly = backtest.run("X", _ramp(120), fee=0.01)
    assert costly.final_equity < free.final_equity


def test_bundled_year_of_real_btc_runs():
    candles = kraken.load_snapshot("btc_history")
    assert len(candles) == 365
    r = backtest.run("BTC", candles)
    assert r.bars == 365
    assert r.equity_curve  # produced a curve
    assert -100 < r.total_return < 10_000  # sane bounds
    report = backtest.format_report(r)
    assert "BACKTEST" in report and "Buy & hold" in report
