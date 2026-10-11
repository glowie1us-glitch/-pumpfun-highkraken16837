# Pump.fun HighKraken Bot

Project for the Pump.fun profile **@highkraken16837**, with GitHub-hosted public-data monitoring, an audit trail, and a paper-trading framework inspired by the six-agent dashboard in the reference video.

## Current implementation scope

- Poll public Pump.fun market endpoints and save timestamped snapshots.
- Store run status, errors, watched coins, and simulated trade decisions in the repository.
- Run on a GitHub Actions schedule and manually from the Actions tab.
- Provide a six-agent pipeline: SCOUT (new tokens), TAPE (trades/volume), WALLET (public-address monitor), RISK (hard limits), EXECUTOR (paper-trade only), AUDITOR (logs and review).
- **Live trading is disabled and no transaction signing is implemented in this starter.** This prevents an accidental trade before the new wallet and strategy are explicitly configured and reviewed.

## Pump.fun profile

Configured handle: `@highkraken16837`

This is project metadata only. It does not prove account ownership or create a Pump.fun OAuth connection. Use Pump.fun's official sign-in/account settings to verify the profile.

## Setup

1. Open **Settings → Actions → General** and permit read/write repository contents so the scheduled workflow can commit snapshots.
2. Open **Actions → Pump.fun public monitor → Run workflow** for a manual run.
3. Inspect `data/latest.json`, `data/events.jsonl`, and `data/paper_trades.jsonl`.
4. Scheduled runs are configured every 15 minutes. GitHub may delay scheduled Actions.
5. Optional GitHub Actions variable `SOLANA_PUBLIC_WALLET`: the public address to watch. Leave blank until the intended alternate wallet is chosen. Never add a seed phrase or private key.

## Reference-video dashboard mapping

- Top metrics: public wallet balance, simulated P&L, paper win rate, observed signals.
- Left panels: balance snapshots, public market/trade feed, and errors.
- Six-agent network: SCOUT, TAPE, WALLET, RISK, EXECUTOR, AUDITOR.
- Activity log and risk guard.
- Metrics are shown as unavailable until backed by actual collected data; no demo profit values are fabricated.

## Live trading gate

Before live execution is considered, explicitly select the alternate public wallet and define max amount per trade, daily loss cap, slippage limit, token/liquidity filters, and whether every trade needs manual approval. Keep signing keys outside GitHub source/history; never put them in commits, issues, logs, or chat. Start in paper mode and verify all risk checks before considering any real transaction.

## Data source

The monitor uses Pump.fun's public frontend API for read-only discovery. This is an undocumented frontend interface and may change or rate-limit requests. API failures are logged; they never trigger a transaction.
