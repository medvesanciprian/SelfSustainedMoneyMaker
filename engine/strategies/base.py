"""Strategy interface: every strategy consumes a numeric series (price or
probability, oldest first) and the current position, and returns a Signal.
This keeps strategies domain-agnostic so the same code can run against crypto,
stock, or prediction-market series."""

from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    action: Action
    reason: str


class Strategy:
    def __init__(self, **params):
        self.params = params

    def decide(self, series: list, holding_position: bool) -> Signal:
        raise NotImplementedError
