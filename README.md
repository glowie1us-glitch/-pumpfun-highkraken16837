# Pump.fun HighKraken Bot

Project for Pump.fun **@highkraken16837**. This repository runs public market monitoring and **paper trading only**. It does not sign transactions or place real orders.

## Current status

- Paper simulator: enabled.
- Live trading: disabled (`execution_enabled: false`).
- Public wallet monitored: `D7we1ffz6S5WkqhNCzLy4REoE1MojT33hZRwmeW7LhiU`.
- Reference budget: $50; protected reserve: $5; maximum paper operating allocation: $45.
- Paper position size: $5; maximum one new simulated entry per cycle.
- Paper take-profit threshold: +10%; stop threshold: -8%; time limit: 24 hours.
- Market-cap proxy P&L is approximate and is **not** a real executable quote or real trading performance.

## Workflow

The GitHub Actions workflow runs every 15 minutes and can be started manually:

1. Poll public Pump.fun currently-live coins.
2. Query the public Solana RPC for the configured wallet's SOL balance.
3. Run the paper simulator against the market snapshot.
4. Commit snapshots and simulation state.

Open **Actions → Pump.fun public monitor → Run workflow**:
https://github.com/glowie1us-glitch/-pumpfun-highkraken16837/actions

The public trades endpoint currently returns 404 in the tested route. That data is marked unavailable; the monitor does not invent trade data.

## Files

- `config/bot.json`: public profile metadata, wallet, risk limits, and six agent roles.
- `scripts/monitor.py`: public market and wallet monitoring.
- `scripts/paper_trader.py`: simulated entry/exit logic only.
- `data/latest.json`: last market and wallet snapshot.
- `data/paper_summary.json`: last simulation summary.
- `data/paper_state.json`: open paper positions and simulation balance state.
- `data/paper_trades.jsonl`: simulated entries and exits.
- `data/events.jsonl`: monitor audit events.

## Paper strategy filters

The starter simulator only considers coins from the public currently-live feed, excludes coins marked complete, banned, or NSFW, requires a market-cap proxy between $5,000 and $30,000, and requires at least 5 SOL of real reserves. It records at most one $5 simulated entry per cycle and uses a 10% take-profit / 8% stop-loss / 24-hour time limit.

This is a testing harness, not a proven profitable strategy. Market-cap changes are used as a proxy, so the simulation ignores real swap price, bonding-curve execution, fees, slippage, priority fees, and failed transactions. Do not interpret paper P&L as expected live P&L.

## Live trading

Real trading is not implemented or enabled. Keep it disabled while testing. Before any live executor is designed, independently validate the data source and strategy, define max daily loss and slippage, and use a secure signing arrangement. Never put a seed phrase or private key in this repository, GitHub variables, issues, or chat.
