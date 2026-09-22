import sqlite3
from collections import defaultdict

FEE_RATE = 0.07

c = sqlite3.connect("data/market.db")
fee = lambda p: FEE_RATE * p * (1 - p)

# every snapshot: (timestamp, expiry) -> list of (strike, bid, ask)
snaps = defaultdict(list)
for ts, close, strike, bid, ask in c.execute(
        """SELECT ts, close_time, strike, yes_bid, yes_ask FROM kalshi_quotes
           WHERE strike IS NOT NULL AND yes_bid > 0 AND yes_ask < 1"""):
    snaps[(ts, close)].append((strike, bid, ask))

hits, scanned = [], 0
for (ts, close), rows in snaps.items():
    rows.sort()
    scanned += 1
    for i, (k_lo, _, ask_lo) in enumerate(rows):
        for k_hi, bid_hi, _ in rows[i + 1:]:
            gross = bid_hi - ask_lo          # sell the far strike, buy the near one
            net = gross - fee(ask_lo) - fee(bid_hi)
            if net > 0:
                hits.append((ts, close, k_lo, k_hi, ask_lo, bid_hi, net))

print(f"scanned {scanned:,} snapshots, {sum(len(v) for v in snaps.values()):,} quotes")
print(f"found {len(hits)} violations net of fees\n")
for ts, close, k_lo, k_hi, ask_lo, bid_hi, net in sorted(hits, key=lambda h: -h[6])[:15]:
    print(f"{ts[:19]} | expiry {close[:16]} | buy {k_lo:,.0f} @ {ask_lo:.2f}"
          f" / sell {k_hi:,.0f} @ {bid_hi:.2f} | net {net:+.3f}")