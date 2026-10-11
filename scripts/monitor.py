#!/usr/bin/env python3
"""Read-only Pump.fun/Solana monitor. Never signs or submits transactions."""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
PROFILE = "@highkraken16837"
PUMP_BASE = "https://frontend-api-v3.pump.fun"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
HEADERS = {"User-Agent": "HighKraken-Pumpfun-Monitor/1.0", "Accept": "application/json"}

def request_json(url: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = dict(HEADERS)
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with urlopen(req, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from {url}")
        return json.loads(resp.read().decode("utf-8"))

def append_jsonl(path: Path, item: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")

def main():
    now = datetime.now(timezone.utc).isoformat()
    wallet = os.getenv("SOLANA_PUBLIC_WALLET", "").strip() or "D7we1ffz6S5WkqhNCzLy4REoE1MojT33hZRwmeW7LhiU"
    event = {"timestamp": now, "profile": PROFILE, "mode": "READ_ONLY_PAPER", "execution_enabled": False}
    try:
        coins = request_json(f"{PUMP_BASE}/coins/currently-live?limit=50&offset=0&includeNsfw=false")
        trades = None
        trades_error = None
        try:
            trades = request_json(f"{PUMP_BASE}/trades/latest")
        except Exception as exc:
            trades_error = str(exc)[:300]
        balance_lamports = None
        balance_error = None
        if wallet:
            try:
                result = request_json(SOLANA_RPC, {
                    "jsonrpc": "2.0", "id": 1, "method": "getBalance",
                    "params": [wallet, {"commitment": "confirmed"}]
                })
                if "error" in result:
                    raise RuntimeError(str(result["error"]))
                balance_lamports = result["result"]["value"]
            except Exception as exc:
                balance_error = str(exc)[:300]
        snapshot = {
            "timestamp": now,
            "profile": PROFILE,
            "source": PUMP_BASE,
            "mode": "READ_ONLY_PAPER",
            "execution_enabled": False,
            "budget_reference_usd": 50,
            "reserve_reference_usd": 5,
            "max_operating_budget_reference_usd": 45,
            "wallet_address": wallet,
            "wallet_balance_lamports": balance_lamports,
            "wallet_balance_sol": None if balance_lamports is None else balance_lamports / 1_000_000_000,
            "wallet_balance_error": balance_error,
            "coins_latest": coins,
            "trades_latest": trades,
            "trades_error": trades_error,
        }
        (DATA / "latest.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        event.update({
            "status": "ok",
            "wallet_balance_available": balance_lamports is not None,
            "coins_payload_type": type(coins).__name__,
            "trades_payload_type": type(trades).__name__ if trades is not None else "unavailable",
            "trades_error": trades_error,
            "execution_enabled": False
        })
        append_jsonl(DATA / "events.jsonl", event)
        print(json.dumps(event))
    except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        event.update({"status": "error", "error": str(exc)[:500]})
        append_jsonl(DATA / "events.jsonl", event)
        print(json.dumps(event), file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
