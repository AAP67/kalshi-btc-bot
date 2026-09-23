import time
from datetime import datetime, timezone
from src.db import connect
from src.index_price import fetch_all, index_price

INTERVAL = 5  # seconds between samples

conn = connect()

while True:
    try:
        prices = fetch_all()
        idx = index_price(prices)
        if idx:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            conn.execute("INSERT INTO index_ticks VALUES (?,?,?,?,?)",
                         (ts, idx, prices.get("coinbase"), prices.get("kraken"),
                          prices.get("bitstamp")))
            conn.commit()
            print(f"{ts} | index ${idx:,.2f} from {len(prices)} sources")
    except Exception as e:
        print("Error:", e)
    time.sleep(INTERVAL)