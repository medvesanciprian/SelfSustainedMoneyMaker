# Self-Sustained Money Maker — paper-trading comparison engine

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

**In production:** [.github/workflows/tick.yml](.github/workflows/tick.yml) runs `python scheduler.py --once`
on a schedule (every 15 min) via GitHub Actions, then commits the updated
SQLite ledgers back to this repo. This is deliberate: it needs no machine of
ours to stay on, and public-repo Actions minutes are free. Trigger a tick
manually with `gh workflow run tick.yml` or from the Actions tab.

**Known issue:** GitHub's `schedule` cron trigger has been unreliable about
firing on its own after this workflow's creation (confirmed via
`actions/runs?event=schedule` repeatedly returning 0, even hours in). Manual
`gh workflow run tick.yml` always works fine — it's specifically the
automatic cron firing that's been flaky. If ticks look sparse, check whether
the schedule has started firing yet before assuming something's broken in the code.

**Locally** (for development/testing, not how it runs in production):

```bash
pip install -r requirements.txt

python scheduler.py --once   # one tick of all four tracks
python scheduler.py --loop   # or run continuously, sleeping between ticks
```

After a few ticks have accumulated:

```bash
python scoreboard.py
```

Prints a comparison table (return %, max drawdown, trade count, win rate) and
writes `logs/equity_curve.png` with all four equity curves overlaid.

```bash
python trade_log.py
```

Prints every trade ever made, across all four tracks, in chronological order,
with the strategy's reasoning for each one (e.g. `RSI(14)=28.4 < oversold
threshold 30`). This is permanent history -- pulled from the same SQLite
ledgers that get committed to the repo every tick, not from ephemeral logs.

## Config

`config/tracks.yaml` holds per-track symbol, fee/slippage assumptions, poll
interval, and the loss-cap threshold. Nothing here should be edited to make a
track "look better" — the point is an honest comparison.

Note: `starting_capital` only seeds a track the *first* time it's created —
once a track's ledger exists, its starting capital is locked in and read from
the ledger itself, not re-read from this file. Editing it later has no effect
on an already-running track (by design, so the loss-cap floor and return%
math can't silently drift out from under a live track).

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
