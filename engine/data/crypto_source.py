"""Crypto OHLCV via ccxt public endpoints. No API key required for market data."""

import ccxt


def fetch_series(symbol: str, exchange_id: str = "kraken", timeframe: str = "15m", limit: int = 60):
    """Returns a list of closing prices, oldest first, and the last price."""
    exchange_cls = getattr(ccxt, exchange_id)
    exchange = exchange_cls({"enableRateLimit": True})
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    closes = [candle[4] for candle in ohlcv]
    return closes, closes[-1]
