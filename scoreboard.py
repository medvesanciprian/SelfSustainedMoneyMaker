"""Reads all track ledgers and prints a comparison table, plus writes an
equity-curve chart to logs/equity_curve.png."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

from engine.ledger import Ledger

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "tracks.yaml"
LOG_DIR = Path(__file__).resolve().parent / "logs"


def max_drawdown(equities: list) -> float:
    peak = equities[0]
    worst = 0.0
    for e in equities:
        peak = max(peak, e)
        drawdown = (peak - e) / peak if peak > 0 else 0.0
        worst = max(worst, drawdown)
    return worst * 100


def win_rate(trades: list) -> float:
    """Approximate: pairs consecutive BUY->SELL and checks if equity_after grew."""
    sells = [t for t in trades if t[1] == "SELL" and t[3] > 0]
    if not sells:
        return float("nan")
    wins = 0
    last_buy_equity = None
    for t in trades:
        side = t[1]
        equity_after = t[6]
        if side == "BUY":
            last_buy_equity = equity_after
        elif side == "SELL" and last_buy_equity is not None:
            if equity_after > last_buy_equity:
                wins += 1
    return 100 * wins / len(sells)


def main():
    config = yaml.safe_load(CONFIG_PATH.read_text())["tracks"]
    rows = []
    plt.figure(figsize=(10, 6))

    for track_name, track_config in config.items():
        starting_capital = track_config["starting_capital"]
        ledger = Ledger(track_name, starting_capital)
        curve = ledger.equity_curve()
        trades = ledger.trades()
        ledger.close()

        if not curve:
            rows.append((track_name, starting_capital, None, None, len(trades), None))
            continue

        equities = [row[2] for row in curve]
        current_equity = equities[-1]
        return_pct = 100 * (current_equity - starting_capital) / starting_capital
        dd = max_drawdown(equities)
        wr = win_rate(trades)

        rows.append((track_name, starting_capital, current_equity, return_pct, len(trades), dd, wr))

        xs = list(range(len(equities)))
        plt.plot(xs, equities, label=track_name)

    header = f"{'Track':<32}{'Start':>8}{'Current':>10}{'Return%':>10}{'Trades':>8}{'MaxDD%':>9}{'Win%':>8}"
    print(header)
    print("-" * len(header))
    for row in rows:
        if row[2] is None:
            print(f"{row[0]:<32}{row[1]:>8.2f}{'--':>10}{'--':>10}{row[4]:>8}{'--':>9}{'--':>8}")
        else:
            name, start, current, ret, n_trades, dd, wr = row
            wr_str = "--" if wr != wr else f"{wr:.1f}"  # NaN check
            print(f"{name:<32}{start:>8.2f}{current:>10.4f}{ret:>+9.2f}%{n_trades:>8}{dd:>8.2f}%{wr_str:>8}")

    plt.axhline(y=config[next(iter(config))]["starting_capital"], color="gray", linestyle="--", linewidth=0.8, label="starting capital")
    plt.xlabel("tick #")
    plt.ylabel("equity ($)")
    plt.title("Paper-trading track comparison")
    plt.legend()
    LOG_DIR.mkdir(exist_ok=True)
    out_path = LOG_DIR / "equity_curve.png"
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    print(f"\nEquity curve chart written to {out_path}")


if __name__ == "__main__":
    main()
