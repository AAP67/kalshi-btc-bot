import sqlite3
from datetime import datetime, timedelta

WINDOW_SEC = 60      # measure moves over this window
TOP_N = 15

c = sqlite3.connect("data/market.db")
iso = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# One price per minute, to keep this fast
rows = c.execute("""SELECT substr(ts, 1, 16) AS minute, AVG(price)
                    FROM btc_ticks GROUP BY minute ORDER BY minute""").fetchall()

moves = []
for (t0, p0), (t1, p1) in zip(rows, rows[1:]):
    pct = (p1 - p0) / p0 * 100
    if abs(pct) > 0:
        moves.append((abs(pct), t1, p0, p1, pct))

moves.sort(reverse=True)
print(f"{len(rows):,} minutes of BTC data, {rows[0][0]} to {rows[-1][0]}\n")
print(f"Largest {TOP_N} one-minute moves:\n")
print(f"{'time (UTC)':<20}{'from':>11}{'to':>11}{'move':>9}")
for _, t, p0, p1, pct in moves[:TOP_N]:
    print(f"{t:<20}{p0:>11,.0f}{p1:>11,.0f}{pct:>+8.2f}%")