import sqlite3
from statistics import median

c = sqlite3.connect("data/market.db")

BANDS = [(0.05, 0.15), (0.15, 0.35), (0.35, 0.65), (0.65, 0.85), (0.85, 0.95)]

rows = c.execute("""SELECT yes_bid, yes_ask, bid_size, ask_size FROM kalshi_quotes
                    WHERE yes_bid > 0 AND yes_ask < 1
                      AND bid_size IS NOT NULL AND ask_size IS NOT NULL""").fetchall()

print(f"{len(rows):,} quotes\n")
print(f"{'price band':<14}{'n':>9}{'med bid sz':>12}{'med ask sz':>12}{'p90 ask':>10}{'med spread':>12}")
for lo, hi in BANDS:
    g = [(b, a, bs, asz) for b, a, bs, asz in rows if lo <= (b + a) / 2 < hi]
    if len(g) < 50:
        continue
    asks = sorted(x[3] for x in g)
    p90 = asks[int(len(asks) * 0.9)]
    print(f"{lo:.2f}-{hi:.2f}{'':<6}{len(g):>9,}"
          f"{median(x[2] for x in g):>12,.0f}{median(x[3] for x in g):>12,.0f}"
          f"{p90:>10,.0f}{median(x[1] - x[0] for x in g):>12.3f}")

print("\nDollar value available at the ask (near the money, 35-65c):")
ntm = [(a, asz) for b, a, bs, asz in rows if 0.35 <= (b + a) / 2 < 0.65]
vals = sorted(a * asz for a, asz in ntm)
for label, q in [("median", 0.5), ("75th pct", 0.75), ("90th pct", 0.9)]:
    print(f"  {label:<10} ${vals[int(len(vals) * q)]:,.0f}")