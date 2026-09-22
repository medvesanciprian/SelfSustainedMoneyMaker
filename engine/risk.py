"""Shared risk controls applied on every tick, regardless of strategy or domain."""

from engine.ledger import Ledger, State
from engine.paper_broker import simulate_fill


def equity_of(state: State, last_price: float) -> float:
    return state.cash + state.position_qty * last_price


def check_loss_cap(
    ledger: Ledger,
    state: State,
    last_price: float,
    starting_capital: float,
    loss_cap_pct: float,
    fee_pct: float = 0.0,
    slippage_pct: float = 0.0,
) -> State:
    """If equity has fallen below loss_cap_pct of starting capital, flatten the position
    and mark the track stopped. A stopped track takes no further action until reset.

    The flatten goes through the same simulate_fill path as a normal exit -- a forced
    stop-loss should not be modeled as *more* favorable (zero fee, zero slippage) than
    a planned exit; if anything a panic exit fares worse in reality."""
    if state.stopped:
        return state

    equity = equity_of(state, last_price)
    floor = starting_capital * (loss_cap_pct / 100.0)
    if equity < floor:
        if state.position_qty > 0:
            qty_flattened = state.position_qty
            fill = simulate_fill("SELL", last_price, qty_flattened, fee_pct, slippage_pct)
            proceeds = fill.price * fill.qty - fill.fee
            state.cash += proceeds
            state.position_qty = 0
            state.position_avg_price = 0
            ledger.record_trade(
                side="SELL",
                price=fill.price,
                qty=qty_flattened,
                fee=fill.fee,
                cash_after=state.cash,
                equity_after=state.cash,
                reason=f"LOSS_CAP_TRIGGERED equity={equity:.4f} floor={floor:.4f}",
            )
        state.stopped = True
    return state
