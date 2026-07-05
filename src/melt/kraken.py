"""Kraken market-data feed.

Uses Kraken's public REST API for OHLC candles (no API key required). Trading
(placing real orders) will use Kraken's private endpoints and your API keys --
that lives behind an explicit, opt-in execution layer and is NOT wired up yet;
this module is read-only market data.

Docs: https://docs.kraken.com/rest/#operation/getOHLCData
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import List

from .models import Candle

PUBLIC_BASE = "https://api.kraken.com/0/public"

# Kraken interval codes are in minutes. Map friendly names -> minutes.
INTERVALS = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}

# A few common friendly symbols -> Kraken pair names.
PAIR_ALIASES = {
    "BTC": "XBTUSD", "BTCUSD": "XBTUSD", "BTC_USDT": "XBTUSD",
    "ETH": "ETHUSD", "ETH_USDT": "ETHUSD",
    "SOL": "SOLUSD", "XRP": "XRPUSD", "ADA": "ADAUSD",
    "DOGE": "XDGUSD", "LINK": "LINKUSD", "DOT": "DOTUSD",
}


def resolve_pair(symbol: str) -> str:
    return PAIR_ALIASES.get(symbol.upper(), symbol.upper())


def fetch_ohlc(symbol: str, interval: str = "1d", timeout: int = 20) -> List[Candle]:
    """Fetch recent OHLC candles for `symbol` from Kraken's public API."""
    pair = resolve_pair(symbol)
    minutes = INTERVALS.get(interval, 1440)
    url = f"{PUBLIC_BASE}/OHLC?pair={pair}&interval={minutes}"
    req = urllib.request.Request(url, headers={"User-Agent": "meltmarketexchange/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    if payload.get("error"):
        raise RuntimeError(f"Kraken API error for {symbol}: {payload['error']}")
    result = payload["result"]
    # The result dict has the pair key plus a "last" key; grab the OHLC rows.
    rows = next(v for k, v in result.items() if k != "last")
    candles: List[Candle] = []
    for row in rows:
        ts, o, h, low, c, _vwap, vol, _count = row
        candles.append(Candle(str(ts), float(o), float(h), float(low), float(c), float(vol)))
    return candles


def load_snapshot(name: str = "btc_snapshot") -> List[Candle]:
    """Load a bundled offline snapshot (real historical data) for demos/tests."""
    path = os.path.join(os.path.dirname(__file__), "data", f"{name}.json")
    with open(path) as fh:
        rows = json.load(fh)
    return [Candle(**row) for row in rows]
