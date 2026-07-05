from melt import kraken
from melt.models import Candle
from melt.signals import analyze


def _uptrend(n=30, start=100.0, step=1.0):
    candles = []
    price = start
    for i in range(n):
        o = price
        price += step
        candles.append(Candle(f"t{i}", o, price + 0.5, o - 0.5, price, 100))
    return candles


def _downtrend(n=30, start=200.0, step=1.0):
    candles = []
    price = start
    for i in range(n):
        o = price
        price -= step
        candles.append(Candle(f"t{i}", o, o + 0.5, price - 0.5, price, 100))
    return candles


def test_strong_uptrend_is_buy():
    sig = analyze("TEST", _uptrend())
    assert sig.action == "BUY"
    assert sig.target > sig.entry > sig.stop
    assert sig.risk_reward > 0


def test_strong_downtrend_is_sell():
    sig = analyze("TEST", _downtrend())
    assert sig.action == "SELL"
    assert sig.target < sig.entry < sig.stop


def test_snapshot_loads_and_analyzes():
    candles = kraken.load_snapshot("btc_snapshot")
    assert len(candles) == 15
    sig = analyze("BTC", candles)
    assert sig.symbol == "BTC"
    assert sig.action in {"BUY", "SELL", "HOLD"}
    assert 0.0 <= sig.confidence <= 1.0


def test_confidence_bounded():
    sig = analyze("TEST", _uptrend(n=50, step=5.0))
    assert 0.0 <= sig.confidence <= 1.0
