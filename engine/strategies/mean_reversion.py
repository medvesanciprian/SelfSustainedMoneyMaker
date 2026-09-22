"""RSI-based mean reversion: buy when oversold, sell when overbought."""

from engine.strategies.base import Action, Signal, Strategy


def _rsi(series: list, period: int) -> float:
    if len(series) < period + 1:
        return 50.0  # neutral until enough data
    deltas = [series[i] - series[i - 1] for i in range(len(series) - period, len(series))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


class MeanReversionStrategy(Strategy):
    def decide(self, series: list, holding_position: bool) -> Signal:
        period = self.params.get("rsi_period", 14)
        oversold = self.params.get("oversold", 30)
        overbought = self.params.get("overbought", 70)

        if len(series) < period + 1:
            return Signal(Action.HOLD, f"insufficient history ({len(series)}/{period})")

        rsi = _rsi(series, period)

        if rsi < oversold and not holding_position:
            return Signal(Action.BUY, f"RSI({period})={rsi:.1f} < oversold threshold {oversold}")
        if rsi > overbought and holding_position:
            return Signal(Action.SELL, f"RSI({period})={rsi:.1f} > overbought threshold {overbought}")
        return Signal(Action.HOLD, f"RSI({period})={rsi:.1f} within range")
