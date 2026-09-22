"""Simulated order execution: fills a market order at the last observed price,
applying a fee and slippage assumption. No real money or accounts involved."""

from dataclasses import dataclass


@dataclass
class Fill:
    side: str          # "BUY" or "SELL"
    price: float        # effective fill price after slippage
    qty: float
    fee: float


def simulate_fill(side: str, last_price: float, qty: float, fee_pct: float, slippage_pct: float) -> Fill:
    slip = last_price * (slippage_pct / 100.0)
    fill_price = last_price + slip if side == "BUY" else last_price - slip
    fill_price = max(fill_price, 0.0001)
    notional = fill_price * qty
    fee = notional * (fee_pct / 100.0)
    return Fill(side=side, price=fill_price, qty=qty, fee=fee)
