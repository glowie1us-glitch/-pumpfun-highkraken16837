#!/usr/bin/env python3
"""Deterministic paper-only Pump.fun simulator. Does not sign or submit transactions."""
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = json.loads((ROOT / "config/bot.json").read_text(encoding="utf-8"))
LATEST = DATA / "latest.json"
STATE = DATA / "paper_state.json"
TRADES = DATA / "paper_trades.jsonl"
BUDGET = float(CONFIG.get("budget_reference_usd", 50))
RESERVE = float(CONFIG.get("risk", {}).get("reserve_usd", 5))
MAX_OPERATING = min(float(CONFIG.get("risk", {}).get("max_operating_budget_usd", 45)), BUDGET - RESERVE)
POSITION_USD = 5.0
MAX_NEW_PER_CYCLE = 1
TAKE_PROFIT_PCT = 0.10
STOP_LOSS_PCT = -0.08
MAX_HOLD_HOURS = 24
MIN_MCAP_USD = 5_000
MAX_MCAP_USD = 30_000
MIN_REAL_SOL_RESERVES_LAMPORTS = 5_000_000_000

def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def append_event(item):
    with TRADES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")

def main():
    now = datetime.now(timezone.utc)
    latest = read_json(LATEST, {})
    coins = latest.get("coins_latest", [])
    if not isinstance(coins, list):
        raise SystemExit("No usable coin list in data/latest.json; paper simulator stopped.")
    state = read_json(STATE, {"mode": "PAPER_ONLY", "cash_usd": BUDGET, "open_positions": {}, "closed_positions": [], "last_cycle": None})
    state["mode"] = "PAPER_ONLY"
    state["execution_enabled"] = False
    state["budget_reference_usd"] = BUDGET
    state["reserve_usd"] = RESERVE
    state["max_operating_budget_usd"] = MAX_OPERATING
    positions = state.setdefault("open_positions", {})
    by_mint = {str(c.get("mint")): c for c in coins if isinstance(c, dict) and c.get("mint")}
    events = []
    realized = 0.0

    # Mark positions using the latest observed USD market cap as a proxy price.
    # This is not an executable quote and ignores fees, slippage, and bonding-curve impact.
    for mint, pos in list(positions.items()):
        coin = by_mint.get(mint)
        if not coin:
            continue
        mcap = coin.get("usd_market_cap") or coin.get("market_cap_usd")
        try:
            current = float(mcap)
            entry = float(pos["entry_market_cap_usd"])
        except (TypeError, ValueError, KeyError):
            continue
        if entry <= 0 or current <= 0:
            continue
        pnl_pct = current / entry - 1
        age = now - datetime.fromisoformat(pos["opened_at"])
        close_reason = "take_profit" if pnl_pct >= TAKE_PROFIT_PCT else "stop_loss" if pnl_pct <= STOP_LOSS_PCT else "time_limit" if age >= timedelta(hours=MAX_HOLD_HOURS) else None
        pos["last_market_cap_usd"] = current
        pos["unrealized_pnl_usd"] = round(float(pos["position_usd"]) * pnl_pct, 4)
        if close_reason:
            pnl_usd = round(float(pos["position_usd"]) * pnl_pct, 4)
            realized += pnl_usd
            closed = {
                "timestamp": now.isoformat(), "event": "PAPER_EXIT", "mint": mint,
                "symbol": pos.get("symbol"), "position_usd": pos["position_usd"],
                "entry_market_cap_usd": entry, "exit_market_cap_usd": current,
                "pnl_pct": round(pnl_pct, 6), "pnl_usd_proxy": pnl_usd,
                "reason": close_reason, "mode": "PAPER_ONLY", "execution_enabled": False
            }
            state.setdefault("closed_positions", []).append(closed)
            events.append(closed)
            del positions[mint]

    used = sum(float(p.get("position_usd", 0)) for p in positions.values())
    available = max(0.0, MAX_OPERATING - used)
    new_count = 0
    if new_count < MAX_NEW_PER_CYCLE and available >= POSITION_USD:
        candidates = []
        for coin in coins:
            if not isinstance(coin, dict):
                continue
            mint = str(coin.get("mint", ""))
            if not mint or mint in positions or coin.get("complete") or coin.get("is_banned") or coin.get("nsfw"):
                continue
            try:
                mcap = float(coin.get("usd_market_cap") or coin.get("market_cap_usd") or 0)
                reserves = int(coin.get("real_sol_reserves") or coin.get("real_quote_reserves") or 0)
            except (TypeError, ValueError):
                continue
            if not (MIN_MCAP_USD <= mcap <= MAX_MCAP_USD):
                continue
            if reserves < MIN_REAL_SOL_RESERVES_LAMPORTS:
                continue
            # Require current/active market evidence from the source payload.
            if coin.get("is_currently_live") is False:
                continue
            candidates.append((int(coin.get("last_trade_timestamp") or 0), coin, mcap))
        candidates.sort(key=lambda item: item[0], reverse=True)
        if candidates:
            _, coin, mcap = candidates[0]
            mint = str(coin["mint"])
            position = {
                "mint": mint, "symbol": coin.get("symbol"), "name": coin.get("name"),
                "position_usd": POSITION_USD, "entry_market_cap_usd": mcap,
                "last_market_cap_usd": mcap, "unrealized_pnl_usd": 0.0,
                "opened_at": now.isoformat(), "mode": "PAPER_ONLY",
                "execution_enabled": False, "price_basis": "usd_market_cap_proxy"
            }
            positions[mint] = position
            available -= POSITION_USD
            new_count += 1
            event = {
                "timestamp": now.isoformat(), "event": "PAPER_ENTRY", "mint": mint,
                "symbol": coin.get("symbol"), "name": coin.get("name"),
                "position_usd": POSITION_USD, "entry_market_cap_usd": mcap,
                "mode": "PAPER_ONLY", "execution_enabled": False,
                "note": "Simulated entry only; market cap is a proxy, not an executable token quote."
            }
            events.append(event)
    for event in events:
        append_event(event)
    state["last_cycle"] = now.isoformat()
    state["open_exposure_usd"] = round(sum(float(p.get("position_usd", 0)) for p in positions.values()), 2)
    state["available_operating_budget_usd"] = round(max(0.0, MAX_OPERATING - state["open_exposure_usd"]), 2)
    state["open_positions"] = positions
    state["closed_positions"] = state.get("closed_positions", [])[-1000:]
    state["execution_enabled"] = False
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "timestamp": now.isoformat(), "mode": "PAPER_ONLY", "execution_enabled": False,
        "coins_seen": len(coins), "events_this_cycle": len(events), "new_entries": new_count,
        "open_positions": len(positions), "open_exposure_usd": state["open_exposure_usd"],
        "available_operating_budget_usd": state["available_operating_budget_usd"],
        "reserve_usd": RESERVE, "take_profit_pct": TAKE_PROFIT_PCT,
        "stop_loss_pct": STOP_LOSS_PCT, "note": "PnL is a market-cap proxy, not realized exchange PnL."
    }
    (DATA / "paper_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))

if __name__ == "__main__":
    main()
