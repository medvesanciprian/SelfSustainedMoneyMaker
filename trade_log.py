"""Prints every trade across all tracks, chronologically, with the strategy's
reasoning for each one. Complements scoreboard.py's summary stats with the
actual decision-by-decision history."""

from engine.config import load_tracks_config
from engine.ledger import Ledger


def main():
    config = load_tracks_config()
    all_trades = []

    for track_name, track_config in config.items():
        ledger = Ledger(track_name, track_config["starting_capital"])
        for ts, side, price, qty, fee, cash_after, equity_after, reason in ledger.trades():
            all_trades.append((ts, track_name, side, price, qty, fee, equity_after, reason))
        ledger.close()

    all_trades.sort(key=lambda t: t[0])

    if not all_trades:
        print("No trades yet.")
        return

    header = f"{'Timestamp (UTC)':<20}{'Track':<30}{'Side':<6}{'Qty':>14}{'Price':>14}{'Fee':>9}{'Equity':>10}  Reason"
    print(header)
    print("-" * len(header))
    for ts, track, side, price, qty, fee, equity_after, reason in all_trades:
        ts_short = ts.split(".")[0].replace("T", " ")  # "2026-09-23 08:21:00", drop microseconds/offset (always UTC)
        print(f"{ts_short:<20}{track:<30}{side:<6}{qty:>14.6f}{price:>14.6f}{fee:>9.4f}{equity_after:>10.4f}  {reason}")

    print(f"\n{len(all_trades)} trade(s) total across {len(config)} tracks.")


if __name__ == "__main__":
    main()
