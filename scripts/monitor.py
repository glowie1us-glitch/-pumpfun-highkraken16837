#!/usr/bin/env python3
"""Read-only Pump.fun market monitor. Never signs or submits transactions."""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
PROFILE = "@highkraken16837"
BASE = "https://frontend-api-v3.pump.fun"
HEADERS = {"User-Agent": "HighKraken-Pumpfun-Monitor/1.0", "Accept": "application/json"}

def get_json(url: str):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from Pump.fun")
        return json.loads(resp.read().decode("utf-8"))

def append_jsonl(path: Path, item: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")

def main():
    now = datetime.now(timezone.utc).isoformat()
    event = {"timestamp": now, "profile": PROFILE, "mode": "READ_ONLY_PAPER", "execution_enabled": False}
    try:
        coins = get_json(f"{BASE}/coins/latest?limit=50&offset=0&includeNsfw=false")
        trades = get_json(f"{BASE}/trades/latest")
        snapshot = {
            "timestamp": now,
            "profile": PROFILE,
            "source": BASE,
            "mode": "READ_ONLY_PAPER",
            "execution_enabled": False,
            "wallet_address": os.getenv("SOLANA_PUBLIC_WALLET", ""),
            "coins_latest": coins,
            "trades_latest": trades,
        }
        (DATA / "latest.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        event.update({"status": "ok", "coins_payload_type": type(coins).__name__, "trades_payload_type": type(trades).__name__})
        append_jsonl(DATA / "events.jsonl", event)
        print(json.dumps({"status": "ok", "timestamp": now, "profile": PROFILE, "mode": "READ_ONLY_PAPER", "execution_enabled": False}))
    except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        event.update({"status": "error", "error": str(exc)[:500]})
        append_jsonl(DATA / "events.jsonl", event)
        print(json.dumps(event), file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
