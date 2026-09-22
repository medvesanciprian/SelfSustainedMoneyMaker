"""SMA-crossover trend-following: buy when the fast SMA is above the slow SMA
(and we're not already in), sell when it crosses back below."""

from engine.strategies.base import Action, Signal, Strategy


def _sma(series: list, window: int) -> float:
    tail = series[-window:]
    return sum(tail) / len(tail)


class MomentumStrategy(Strategy):
    def decide(self, series: list, holding_position: bool) -> Signal:
        fast_window = self.params.get("fast_window", 5)
        slow_window = self.params.get("slow_window", 20)

        if len(series) < slow_window + 1:
            return Signal(Action.HOLD, f"insufficient history ({len(series)}/{slow_window})")

        fast_now = _sma(series, fast_window)
        slow_now = _sma(series, slow_window)
        fast_prev = _sma(series[:-1], fast_window)
        slow_prev = _sma(series[:-1], slow_window)

        crossed_up = fast_prev <= slow_prev and fast_now > slow_now
        crossed_down = fast_prev >= slow_prev and fast_now < slow_now

        if crossed_up and not holding_position:
            return Signal(Action.BUY, f"fast SMA({fast_window})={fast_now:.6f} crossed above slow SMA({slow_window})={slow_now:.6f}")
        if crossed_down and holding_position:
            return Signal(Action.SELL, f"fast SMA({fast_window})={fast_now:.6f} crossed below slow SMA({slow_window})={slow_now:.6f}")
        return Signal(Action.HOLD, "no crossover")
