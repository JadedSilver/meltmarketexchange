import math

from melt import indicators as ind


def test_sma_basic():
    assert ind.sma([1, 2, 3, 4], 2) == 3.5
    assert ind.sma([1, 2], 5) is None


def test_ema_converges_toward_series():
    # A constant series has EMA equal to that constant.
    assert ind.ema([5, 5, 5, 5, 5], 3) == 5


def test_rsi_all_gains_is_100():
    values = list(range(1, 20))  # strictly increasing
    assert ind.rsi(values, 14) == 100.0


def test_rsi_known_range():
    values = [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10,
              45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
    r = ind.rsi(values, 14)
    assert r is not None and 60 < r < 80


def test_atr_positive():
    highs = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
    lows = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    closes = [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5,
              19.5, 20.5, 21.5, 22.5, 23.5, 24.5]
    a = ind.atr(highs, lows, closes, 14)
    assert a is not None and a > 0


def test_macd_returns_values_for_long_series():
    values = [float(x) for x in range(1, 60)]
    line, signal, hist = ind.macd(values)
    assert line is not None and signal is not None
    assert not math.isnan(hist)
