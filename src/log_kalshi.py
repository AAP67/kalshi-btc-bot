import time
from datetime import datetime, timezone
from src.db import connect
from src.kalshi_client import KalshiClient

INTERVAL = 10  # seconds between snapshots
client = KalshiClient("prod", auth=False)
conn = connect()


def num(x):
    return float(x) if x not in (None, "") else None


while True:
    try:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        rows = [
            (ts, m["ticker"], m.get("event_ticker"), num(m.get("floor_strike")),
             m.get("close_time"), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars")),
             num(m.get("yes_bid_size_fp")), num(m.get("yes_ask_size_fp")))
            for m in client.get_markets(limit=1000)
        ]
        conn.executemany("INSERT INTO kalshi_quotes VALUES (?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        print(f"{ts} | saved {len(rows)} quotes")
    except Exception as e:
        print("Error:", e)
    time.sleep(INTERVAL)