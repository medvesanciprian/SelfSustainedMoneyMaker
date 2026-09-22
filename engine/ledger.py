"""SQLite-backed ledger: cash, position, trade history, equity curve, per track."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DATA_STORE = Path(__file__).resolve().parent.parent / "data_store"


@dataclass
class State:
    cash: float
    position_qty: float
    position_avg_price: float
    stopped: bool


class Ledger:
    def __init__(self, track_name: str, starting_capital: float):
        DATA_STORE.mkdir(exist_ok=True)
        self.track_name = track_name
        self.db_path = DATA_STORE / f"{track_name}.db"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cash REAL NOT NULL,
                position_qty REAL NOT NULL,
                position_avg_price REAL NOT NULL,
                stopped INTEGER NOT NULL
            )"""
        )
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                qty REAL NOT NULL,
                fee REAL NOT NULL,
                cash_after REAL NOT NULL,
                equity_after REAL NOT NULL,
                reason TEXT
            )"""
        )
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                price REAL,
                equity REAL NOT NULL
            )"""
        )
        self._conn.commit()

        row = self._conn.execute("SELECT cash, position_qty, position_avg_price, stopped FROM state WHERE id = 1").fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO state (id, cash, position_qty, position_avg_price, stopped) VALUES (1, ?, 0, 0, 0)",
                (starting_capital,),
            )
            self._conn.commit()

    def get_state(self) -> State:
        row = self._conn.execute(
            "SELECT cash, position_qty, position_avg_price, stopped FROM state WHERE id = 1"
        ).fetchone()
        return State(cash=row[0], position_qty=row[1], position_avg_price=row[2], stopped=bool(row[3]))

    def set_state(self, state: State):
        self._conn.execute(
            "UPDATE state SET cash = ?, position_qty = ?, position_avg_price = ?, stopped = ? WHERE id = 1",
            (state.cash, state.position_qty, state.position_avg_price, int(state.stopped)),
        )
        self._conn.commit()

    def record_trade(self, side: str, price: float, qty: float, fee: float, cash_after: float, equity_after: float, reason: str = ""):
        self._conn.execute(
            "INSERT INTO trades (ts, side, price, qty, fee, cash_after, equity_after, reason) VALUES (?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), side, price, qty, fee, cash_after, equity_after, reason),
        )
        self._conn.commit()

    def record_equity(self, price: float, equity: float):
        self._conn.execute(
            "INSERT INTO equity_curve (ts, price, equity) VALUES (?,?,?)",
            (datetime.now(timezone.utc).isoformat(), price, equity),
        )
        self._conn.commit()

    def equity_curve(self):
        return self._conn.execute("SELECT ts, price, equity FROM equity_curve ORDER BY id").fetchall()

    def trades(self):
        return self._conn.execute("SELECT ts, side, price, qty, fee, cash_after, equity_after, reason FROM trades ORDER BY id").fetchall()

    def close(self):
        self._conn.close()
