"""One tick of one track: fetch data -> risk check -> strategy -> paper broker -> ledger."""

import logging

from engine.ledger import Ledger
from engine.paper_broker import simulate_fill
from engine.risk import check_loss_cap, equity_of
from engine.strategies.base import Action
from engine.strategies.mean_reversion import MeanReversionStrategy
from engine.strategies.momentum import MomentumStrategy

STRATEGIES = {
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
}

logger = logging.getLogger(__name__)


def run_tick(track_name: str, config: dict, fetch_series_fn):
    """fetch_series_fn() -> (series: list[float], last_price: float).
    Isolated per track: exceptions are caught by the caller (scheduler)."""

    starting_capital = config["starting_capital"]
    fee_pct = config["fee_pct"]
    slippage_pct = config["slippage_pct"]
    loss_cap_pct = config["loss_cap_pct"]

    ledger = Ledger(track_name, starting_capital)
    state = ledger.get_state()

    if state.stopped:
        logger.info("[%s] track is stopped (loss cap previously triggered); skipping", track_name)
        ledger.close()
        return

    series, last_price = fetch_series_fn()

    state = check_loss_cap(ledger, state, last_price, starting_capital, loss_cap_pct)
    ledger.set_state(state)
    if state.stopped:
        logger.warning("[%s] LOSS CAP TRIGGERED at price %.6f", track_name, last_price)
        ledger.record_equity(last_price, equity_of(state, last_price))
        ledger.close()
        return

    strategy_cls = STRATEGIES[config["strategy"]]
    strategy = strategy_cls(**config.get("strategy_params", {}))
    holding_position = state.position_qty > 0
    signal = strategy.decide(series, holding_position)

    if signal.action == Action.BUY and not holding_position:
        qty = state.cash / last_price
        fill = simulate_fill("BUY", last_price, qty, fee_pct, slippage_pct)
        cost = fill.price * fill.qty + fill.fee
        if cost <= state.cash:
            state.cash -= cost
            state.position_qty = fill.qty
            state.position_avg_price = fill.price
            equity = equity_of(state, last_price)
            ledger.record_trade("BUY", fill.price, fill.qty, fill.fee, state.cash, equity, signal.reason)
            logger.info("[%s] BUY %.6f @ %.6f (fee %.6f) -> equity %.4f", track_name, fill.qty, fill.price, fill.fee, equity)

    elif signal.action == Action.SELL and holding_position:
        qty = state.position_qty
        fill = simulate_fill("SELL", last_price, qty, fee_pct, slippage_pct)
        proceeds = fill.price * fill.qty - fill.fee
        state.cash += proceeds
        state.position_qty = 0
        state.position_avg_price = 0
        equity = state.cash
        ledger.record_trade("SELL", fill.price, fill.qty, fill.fee, state.cash, equity, signal.reason)
        logger.info("[%s] SELL %.6f @ %.6f (fee %.6f) -> equity %.4f", track_name, fill.qty, fill.price, fill.fee, equity)

    else:
        logger.info("[%s] HOLD @ %.6f (%s)", track_name, last_price, signal.reason)

    ledger.set_state(state)
    ledger.record_equity(last_price, equity_of(state, last_price))
    ledger.close()
