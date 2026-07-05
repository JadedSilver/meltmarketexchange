"""Command-line entry point for the melt trading assistant.

Commands:
  melt morning [--watchlist BTC,ETH,...]   Live Kraken briefing of today's plays
  melt scan SYMBOL                         Deep-dive one instrument (live)
  melt demo                                Offline briefing on bundled real data
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from . import kraken
from .briefing import DEFAULT_WATCHLIST, format_briefing, scan
from .signals import analyze


def _parse_watchlist(raw: str | None) -> List[str]:
    if not raw:
        return DEFAULT_WATCHLIST
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def cmd_morning(args: argparse.Namespace) -> int:
    watchlist = _parse_watchlist(args.watchlist)
    print(f"Fetching live Kraken data for {len(watchlist)} instruments...\n")
    signals = scan(watchlist, lambda sym: kraken.fetch_ohlc(sym, args.interval))
    if not signals:
        print("No data returned. Check connectivity to api.kraken.com.")
        return 1
    print(format_briefing(signals))
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    candles = kraken.fetch_ohlc(args.symbol, args.interval)
    sig = analyze(args.symbol.upper(), candles)
    print(format_briefing([sig]))
    return 0


def cmd_demo(_args: argparse.Namespace) -> int:
    print("Offline demo using a bundled real BTC/USD daily snapshot.\n")
    candles = kraken.load_snapshot("btc_snapshot")
    sig = analyze("BTC", candles)
    print(format_briefing([sig]))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="melt", description="Melt Market Exchange trading assistant")
    sub = p.add_subparsers(dest="command", required=True)

    m = sub.add_parser("morning", help="Live morning briefing over a watchlist")
    m.add_argument("--watchlist", help="Comma-separated symbols (default: majors)")
    m.add_argument("--interval", default="1d", help="Candle interval (default 1d)")
    m.set_defaults(func=cmd_morning)

    s = sub.add_parser("scan", help="Analyze a single symbol live")
    s.add_argument("symbol")
    s.add_argument("--interval", default="1d", help="Candle interval (default 1d)")
    s.set_defaults(func=cmd_scan)

    d = sub.add_parser("demo", help="Offline briefing on bundled real data")
    d.set_defaults(func=cmd_demo)
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
