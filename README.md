# Self-Sustained Money Maker — paper-trading comparison engine
<!-- race-test marker, safe to remove -->


**Status: validation phase.** This is a paper-trading (simulated money) comparison
engine. No exchange or broker accounts, no API keys, no real capital involved yet.
The goal is to run four strategies in parallel against live public market data and
see which one actually holds up before ever risking the real $10.

## What it does

Four tracks, each starting from a simulated $10, all sharing one engine:

| Track | Domain | Data source (free, no key) | Strategy |
|---|---|---|---|
| `crypto_momentum` | Crypto (BTC/USD, Kraken) | `ccxt` public OHLCV | SMA crossover trend-following |
| `crypto_mean_reversion` | Crypto (ETH/USD, Kraken) | `ccxt` public OHLCV | RSI(14) oversold/overbought |
| `stocks_momentum` | Stocks (SPY) | `yfinance` | SMA crossover trend-following |
| `prediction_markets_momentum` | Prediction markets | Polymarket Gamma API | SMA crossover on implied probability |

Every tick: fetch the latest price series → check the per-track loss cap (flattens
and stops the track if equity falls below 50% of starting capital) → run the
strategy → simulate a fill (with fee + slippage) → log the trade and equity to a
per-track SQLite ledger in `data_store/`.

## Running it

```bash
pip install -r requirements.txt

# One tick of all four tracks (recommended: schedule this every 15 min via
# Windows Task Scheduler, cron, etc. — more robust than a long-lived process)
python scheduler.py --once

# Or run continuously, sleeping between ticks:
python scheduler.py --loop
```

After a few ticks have accumulated:

```bash
python scoreboard.py
```

Prints a comparison table (return %, max drawdown, trade count, win rate) and
writes `logs/equity_curve.png` with all four equity curves overlaid.

## Config

`config/tracks.yaml` holds per-track symbol, fee/slippage assumptions, poll
interval, and the loss-cap threshold. Nothing here should be edited to make a
track "look better" — the point is an honest comparison.

## What's deliberately not here yet

Real exchange/broker accounts, API keys, real order execution. Those only get
added once the scoreboard shows a track worth funding with the actual $10 — a
decision to make together after seeing real data, not something the app decides
on its own.

## Dev agents

`.claude/agents/` has ~155 specialized Claude Code subagent personas (from
[agency-agents](https://github.com/msitarzewski/agency-agents), installed
locally to this project only) covering engineering, finance, security, testing,
research, and product — useful for reviewing strategy logic, auditing secrets
handling before the real-money phase, etc. They are prompt personas for
development assistance, not part of the runtime engine.
