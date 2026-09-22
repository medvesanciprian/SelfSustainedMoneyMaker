"""Stock OHLCV via yfinance. No API key required."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

import yfinance as yf

NY_TZ = ZoneInfo("America/New_York")


def market_is_open(now=None) -> bool:
    """Rough NYSE regular-hours check: Mon-Fri, 09:30-16:00 America/New_York.
    Does not account for market holidays -- a closed-market tick will simply
    fail to find fresh data and no-op, which is an acceptable approximation."""
    now = now or datetime.now(NY_TZ)
    if now.weekday() >= 5:
        return False
    return time(9, 30) <= now.time() <= time(16, 0)


def fetch_series(symbol: str, period: str = "5d", interval: str = "15m"):
    """Returns a list of closing prices, oldest first, and the last price."""
    hist = yf.Ticker(symbol).history(period=period, interval=interval)
    closes = hist["Close"].dropna().tolist()
    if not closes:
        raise RuntimeError(f"No price data returned for {symbol}")
    return closes, closes[-1]
