import sqlite3, sys
from datetime import datetime, timezone, timedelta
from statistics import mean
from src.pricing import prob_above

DIM = sys.argv[1] if len(sys.argv) > 1 else "move"    # move | spread | price
LEAD_MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 30
VOL = 0.35
LOOKBACK_MIN = 5

BUCKETS = {
    "move":   ([0.05, 0.15, 0.35], "BTC move in prior 5 min (%)"),
    "spread": ([0.015, 0.025, 0.045], "ask - bid (cents)"),
    "price":  ([0.05, 0.15, 0.35], "market mid price"),
}
edges_in, label = BUCKETS[DIM]

c = sqlite3.connect("data/market.db")
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
iso = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def price_at(ts):
    r = c.execute("SELECT price FROM btc_ticks WHERE ts <= ? ORDER BY ts DESC LIMIT 1", (ts,)).fetchone()
    return r[0] if r else None


samples = []
for (close,) in c.execute(
        "SELECT DISTINCT close_time FROM kalshi_quotes WHERE close_time < ? ORDER BY close_time", (now,)):
    settle = price_at(close)
    if not settle:
        continue
    close_dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
    ts = c.execute("SELECT MAX(ts) FROM kalshi_quotes WHERE close_time = ? AND ts <= ?",
                   (close, iso(close_dt - timedelta(minutes=LEAD_MIN)))).fetchone()[0]
    if not ts:
        continue
    spot = price_at(ts)
    prior = price_at(iso(datetime.fromisoformat(ts.replace("Z", "+00:00")) - timedelta(minutes=LOOKBACK_MIN)))
    if not spot or not prior:
        continue
    move = abs(spot - prior) / prior * 100
    years = LEAD_MIN * 60 / (365 * 24 * 3600)

    for strike, bid, ask in c.execute(
            """SELECT strike, yes_bid, yes_ask FROM kalshi_quotes
               WHERE close_time = ? AND ts = ? AND yes_bid > 0 AND yes_ask < 1""", (close, ts)):
        if strike is None:
            continue
        mid = (bid + ask) / 2
        key = {"move": move, "spread": ask - bid, "price": min(mid, 1 - mid)}[DIM]
        samples.append((key, mid, prob_above(spot, strike, years, VOL),
                        1.0 if settle > strike else 0.0))

if not samples:
    print("No settled contracts logged yet.")
    raise SystemExit

print(f"{len(samples)} outcomes | {LEAD_MIN} min before close | model vol {VOL:.0%}")
print(f"split by: {label}\n")
print(f"{'bucket':<16}{'n':>6}{'market':>9}{'model':>9}{'winner':>9}")
bounds = [0] + edges_in + [999]
for lo, hi in zip(bounds, bounds[1:]):
    g = [s for s in samples if lo <= s[0] < hi]
    if len(g) < 20:
        continue
    mkt = mean((s[1] - s[3]) ** 2 for s in g)
    mdl = mean((s[2] - s[3]) ** 2 for s in g)
    name = f"{lo:g} - {hi:g}" if hi < 999 else f"{lo:g}+"
    print(f"{name:<16}{len(g):>6}{mkt:>9.4f}{mdl:>9.4f}{'market' if mkt < mdl else 'MODEL':>9}")