import time
from datetime import datetime, timezone
from src.kalshi_client import KalshiClient

SECONDS = 120
INTERVAL = 2

client = KalshiClient("prod", auth=False)


def num(x):
    return float(x) if x not in (None, "") else None


# Pick a liquid near-the-money contract from the nearest expiry
mkts = [m for m in client.get_markets(limit=1000)
        if num(m.get("yes_bid")) or num(m.get("yes_bid_dollars"))]
mkts = [m for m in mkts if 0.2 < num(m.get("yes_bid_dollars") or 0) < 0.8]
mkts.sort(key=lambda m: m["close_time"])
ticker = mkts[0]["ticker"]
print(f"Probing {ticker} every {INTERVAL}s for {SECONDS}s")
print("A = /markets list endpoint, B = /markets/{ticker} single endpoint\n")
print(f"{'time':<10}{'A bid':>8}{'A ask':>8}{'B bid':>8}{'B ask':>8}  changed")

prev = None
end = time.time() + SECONDS
while time.time() < end:
    t = datetime.now(timezone.utc).strftime("%H:%M:%S")
    a = client.get("/markets", {"tickers": ticker})["markets"][0]
    b = client.get(f"/markets/{ticker}")["market"]
    cur = (num(a.get("yes_bid_dollars")), num(a.get("yes_ask_dollars")),
           num(b.get("yes_bid_dollars")), num(b.get("yes_ask_dollars")))
    changed = ""
    if prev:
        if cur[:2] != prev[:2]:
            changed += "A "
        if cur[2:] != prev[2:]:
            changed += "B"
    print(f"{t:<10}" + "".join(f"{v:>8.2f}" if v is not None else f"{'-':>8}" for v in cur) + f"  {changed}")
    prev = cur
    time.sleep(INTERVAL)